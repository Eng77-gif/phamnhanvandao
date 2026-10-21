-- =====================================================================
-- THẾ GIỚI TRỰC TUYẾN — Bang Hội, Lôi Đài, Kênh Chat
-- Chỉ thêm bảng/hàm mới, không đụng tới bảng cũ. Mọi thao tác ghi đi qua
-- hàm SECURITY DEFINER; người chơi chỉ được đọc.
-- (Vị trí người chơi trên bản đồ 2D dùng Realtime Presence, không cần bảng.)
-- =====================================================================

create table if not exists public.guilds (
  id bigint generated always as identity primary key,
  name text not null unique,
  tag text not null unique,
  leader uuid not null references auth.users(id) on delete cascade,
  notice text not null default '',
  fund bigint not null default 0,
  level int not null default 1,
  created_at timestamptz not null default now()
);
create table if not exists public.guild_members (
  user_id uuid primary key references auth.users(id) on delete cascade,
  guild_id bigint not null references public.guilds(id) on delete cascade,
  role text not null default 'member' check (role in ('leader','elder','member')),
  name text not null,
  realm_idx int not null default 0,
  contribution bigint not null default 0,
  joined_at timestamptz not null default now()
);
create index if not exists guild_members_guild_idx on public.guild_members(guild_id);

create table if not exists public.world_chat (
  id bigint generated always as identity primary key,
  user_id uuid not null references auth.users(id) on delete cascade,
  channel text not null,
  name text not null,
  realm_idx int not null default 0,
  tag text,
  body text not null,
  created_at timestamptz not null default now()
);
create index if not exists world_chat_ch_idx on public.world_chat(channel, id desc);
create index if not exists world_chat_user_idx on public.world_chat(user_id, created_at desc);

create table if not exists public.arena_challenges (
  id bigint generated always as identity primary key,
  challenger uuid not null references auth.users(id) on delete cascade,
  target uuid not null references auth.users(id) on delete cascade,
  c_name text not null,
  t_name text not null,
  status text not null default 'pending' check (status in ('pending','declined','done','expired','cancelled')),
  result jsonb,
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);
create index if not exists arena_ch_target_idx on public.arena_challenges(target, status);
create index if not exists arena_ch_chal_idx on public.arena_challenges(challenger, created_at desc);

create table if not exists public.arena_stats (
  user_id uuid primary key references auth.users(id) on delete cascade,
  name text not null,
  realm_idx int not null default 0,
  points int not null default 1000,
  wins int not null default 0,
  losses int not null default 0,
  updated_at timestamptz not null default now()
);
create index if not exists arena_stats_pts_idx on public.arena_stats(points desc);

alter table public.guilds enable row level security;
alter table public.guild_members enable row level security;
alter table public.world_chat enable row level security;
alter table public.arena_challenges enable row level security;
alter table public.arena_stats enable row level security;

drop policy if exists "guilds read" on public.guilds;
create policy "guilds read" on public.guilds for select to authenticated using (true);
drop policy if exists "guild members read" on public.guild_members;
create policy "guild members read" on public.guild_members for select to authenticated using (true);
drop policy if exists "arena stats read" on public.arena_stats;
create policy "arena stats read" on public.arena_stats for select to authenticated using (true);
drop policy if exists "arena own read" on public.arena_challenges;
create policy "arena own read" on public.arena_challenges for select to authenticated using (auth.uid() = challenger or auth.uid() = target);
drop policy if exists "chat read" on public.world_chat;
create policy "chat read" on public.world_chat for select to authenticated using (
  channel = 'world' or channel = 'g' || (select gm.guild_id::text from public.guild_members gm where gm.user_id = auth.uid())
);

-- Thông tin công khai của một người chơi, lấy thẳng từ bản lưu trên máy chủ
create or replace function public._wo_me(uid uuid, out st jsonb, out nm text, out realm int)
language plpgsql stable security definer set search_path to 'public' as $$
begin
  select data->'state' into st from public.saves where user_id = uid;
  if st is null then raise exception 'Chưa có bản lưu trên đám mây'; end if;
  if st->'root' is null or jsonb_typeof(st->'root') <> 'object' then raise exception 'Nhân vật chưa nhập đạo'; end if;
  nm := left(coalesce(nullif(st->>'name',''),'Vô Danh'), 24);
  realm := least(12, greatest(0, coalesce((st->>'realmIdx')::int,0)));
end; $$;

create or replace function public._guild_level(f bigint) returns int language sql immutable as $$
  select case when f >= 1500000 then 5 when f >= 600000 then 4 when f >= 200000 then 3 when f >= 50000 then 2 else 1 end;
$$;
create or replace function public._guild_cap(lv int) returns int language sql immutable as $$ select 10 + 5*(lv-1); $$;

/* ------------------------------ KÊNH CHAT ------------------------------ */
create or replace function public.chat_send(p_channel text, p_body text)
returns public.world_chat language plpgsql security definer set search_path to 'public' as $$
declare me uuid := auth.uid(); p record; ch text; g public.guild_members; tg text; r public.world_chat; b text; n int;
begin
  perform public._need_real(); perform public._require_clean();
  b := btrim(regexp_replace(coalesce(p_body,''), '\s+', ' ', 'g'));
  if length(b) < 1 then raise exception 'Tin nhắn trống'; end if;
  if length(b) > 200 then b := left(b, 200); end if;
  select * into p from public._wo_me(me);
  select * into g from public.guild_members where user_id = me;
  if p_channel = 'guild' then
    if g.user_id is null then raise exception 'Ngươi chưa gia nhập bang hội nào'; end if;
    ch := 'g' || g.guild_id;
  else ch := 'world'; end if;
  if exists (select 1 from public.world_chat where user_id = me and created_at > now() - interval '3 seconds') then
    raise exception 'Nói chậm thôi — đợi vài giây rồi gửi tiếp'; end if;
  select count(*) into n from public.world_chat where user_id = me and created_at > now() - interval '1 minute';
  if n >= 15 then raise exception 'Gửi quá nhiều tin trong một phút'; end if;
  if g.user_id is not null then select tag into tg from public.guilds where id = g.guild_id; end if;
  insert into public.world_chat(user_id, channel, name, realm_idx, tag, body) values (me, ch, p.nm, p.realm, tg, b) returning * into r;
  if r.id % 50 = 0 then delete from public.world_chat where channel = ch and id < r.id - 500; end if;
  return r;
end; $$;

/* ------------------------------ BANG HỘI ------------------------------ */
create or replace function public.guild_state()
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare me uuid := auth.uid(); m public.guild_members; g public.guilds; p record; mem jsonb;
begin
  perform public._need_real();
  select * into m from public.guild_members where user_id = me;
  if not found then return jsonb_build_object('guild', null); end if;
  begin
    select * into p from public._wo_me(me);
    update public.guild_members set name = p.nm, realm_idx = p.realm where user_id = me;
  exception when others then null; end;
  select * into g from public.guilds where id = m.guild_id;
  select coalesce(jsonb_agg(jsonb_build_object('user_id', x.user_id, 'name', x.name, 'realm_idx', x.realm_idx, 'role', x.role, 'contribution', x.contribution)
    order by case x.role when 'leader' then 0 when 'elder' then 1 else 2 end, x.contribution desc), '[]'::jsonb)
    into mem from public.guild_members x where x.guild_id = g.id;
  return jsonb_build_object('guild', to_jsonb(g), 'role', m.role, 'cap', public._guild_cap(g.level), 'members', mem);
end; $$;

create or replace function public.guild_list()
returns jsonb language sql stable security definer set search_path to 'public' as $$
  select coalesce(jsonb_agg(t order by (t->>'level')::int desc, (t->>'fund')::bigint desc), '[]'::jsonb) from (
    select jsonb_build_object('id', g.id, 'name', g.name, 'tag', g.tag, 'level', g.level, 'fund', g.fund, 'notice', g.notice,
      'cap', public._guild_cap(g.level), 'count', (select count(*) from public.guild_members x where x.guild_id = g.id),
      'leader', (select x.name from public.guild_members x where x.user_id = g.leader)) t
    from public.guilds g order by g.level desc, g.fund desc limit 60) s;
$$;

create or replace function public.guild_create(p_name text, p_tag text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare me uuid := auth.uid(); p record; nm text := btrim(coalesce(p_name,'')); tg text := upper(btrim(coalesce(p_tag,''))); gid bigint; rev int;
begin
  perform public._need_real(); perform public._require_clean();
  if exists (select 1 from public.guild_members where user_id = me) then raise exception 'Ngươi đã ở trong một bang hội'; end if;
  if length(nm) < 2 or length(nm) > 20 then raise exception 'Tên bang từ 2 đến 20 ký tự'; end if;
  if length(tg) < 1 or length(tg) > 4 then raise exception 'Hiệu bang từ 1 đến 4 ký tự'; end if;
  if exists (select 1 from public.guilds where lower(name) = lower(nm)) then raise exception 'Tên bang đã có người dùng'; end if;
  if exists (select 1 from public.guilds where upper(tag) = tg) then raise exception 'Hiệu bang đã có người dùng'; end if;
  select * into p from public._wo_me(me);
  if p.realm < 1 then raise exception 'Cần đạt Trúc Cơ mới đủ uy vọng khai lập bang hội'; end if;
  rev := public._inv_add(me, array['state','spiritStones'], -5000);
  insert into public.guilds(name, tag, leader) values (nm, tg, me) returning id into gid;
  insert into public.guild_members(user_id, guild_id, role, name, realm_idx) values (me, gid, 'leader', p.nm, p.realm);
  return jsonb_build_object('rev', rev, 'id', gid);
end; $$;

create or replace function public.guild_join(p_id bigint)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare me uuid := auth.uid(); p record; g public.guilds; n int;
begin
  perform public._need_real(); perform public._require_clean();
  if exists (select 1 from public.guild_members where user_id = me) then raise exception 'Ngươi đã ở trong một bang hội'; end if;
  select * into g from public.guilds where id = p_id for update;
  if not found then raise exception 'Bang hội không tồn tại'; end if;
  select count(*) into n from public.guild_members where guild_id = g.id;
  if n >= public._guild_cap(g.level) then raise exception 'Bang hội đã đủ người'; end if;
  select * into p from public._wo_me(me);
  insert into public.guild_members(user_id, guild_id, role, name, realm_idx) values (me, g.id, 'member', p.nm, p.realm);
  return public.guild_state();
end; $$;

create or replace function public.guild_leave()
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare me uuid := auth.uid(); m public.guild_members; heir uuid;
begin
  perform public._need_real();
  select * into m from public.guild_members where user_id = me;
  if not found then raise exception 'Ngươi chưa gia nhập bang hội nào'; end if;
  delete from public.guild_members where user_id = me;
  if m.role = 'leader' then
    select user_id into heir from public.guild_members where guild_id = m.guild_id
      order by case role when 'elder' then 0 else 1 end, contribution desc, joined_at limit 1;
    if heir is null then delete from public.guilds where id = m.guild_id;
    else
      update public.guild_members set role = 'leader' where user_id = heir;
      update public.guilds set leader = heir where id = m.guild_id;
    end if;
  end if;
  return jsonb_build_object('guild', null);
end; $$;

create or replace function public.guild_kick(p_uid uuid)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare me uuid := auth.uid(); m public.guild_members; t public.guild_members;
begin
  perform public._need_real();
  select * into m from public.guild_members where user_id = me;
  select * into t from public.guild_members where user_id = p_uid;
  if m.user_id is null or t.user_id is null or m.guild_id <> t.guild_id or p_uid = me then raise exception 'Không thể trục xuất'; end if;
  if not (m.role = 'leader' or (m.role = 'elder' and t.role = 'member')) then raise exception 'Không đủ quyền'; end if;
  delete from public.guild_members where user_id = p_uid;
  return public.guild_state();
end; $$;

create or replace function public.guild_set_role(p_uid uuid, p_role text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare me uuid := auth.uid(); m public.guild_members; t public.guild_members;
begin
  perform public._need_real();
  select * into m from public.guild_members where user_id = me;
  select * into t from public.guild_members where user_id = p_uid;
  if m.user_id is null or m.role <> 'leader' then raise exception 'Chỉ bang chủ mới được phong chức'; end if;
  if t.user_id is null or t.guild_id <> m.guild_id or p_uid = me then raise exception 'Thành viên không hợp lệ'; end if;
  if p_role = 'leader' then
    update public.guild_members set role = 'elder' where user_id = me;
    update public.guild_members set role = 'leader' where user_id = p_uid;
    update public.guilds set leader = p_uid where id = m.guild_id;
  elsif p_role in ('elder','member') then
    if p_role = 'elder' and (select count(*) from public.guild_members where guild_id = m.guild_id and role = 'elder') >= 3 then
      raise exception 'Mỗi bang tối đa ba trưởng lão'; end if;
    update public.guild_members set role = p_role where user_id = p_uid;
  else raise exception 'Chức vị không hợp lệ'; end if;
  return public.guild_state();
end; $$;

create or replace function public.guild_donate(p_amount integer)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare me uuid := auth.uid(); m public.guild_members; rev int; f bigint; lv int;
begin
  perform public._need_real(); perform public._require_clean();
  if p_amount is null or p_amount < 100 or p_amount > 1000000 then raise exception 'Số linh thạch không hợp lệ'; end if;
  select * into m from public.guild_members where user_id = me;
  if not found then raise exception 'Ngươi chưa gia nhập bang hội nào'; end if;
  rev := public._inv_add(me, array['state','spiritStones'], -p_amount);
  update public.guild_members set contribution = contribution + p_amount where user_id = me;
  update public.guilds set fund = fund + p_amount where id = m.guild_id returning fund into f;
  lv := public._guild_level(f);
  update public.guilds set level = lv where id = m.guild_id;
  return jsonb_build_object('rev', rev, 'fund', f, 'level', lv);
end; $$;

create or replace function public.guild_notice(p_text text)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare me uuid := auth.uid(); m public.guild_members;
begin
  perform public._need_real();
  select * into m from public.guild_members where user_id = me;
  if m.user_id is null or m.role not in ('leader','elder') then raise exception 'Không đủ quyền'; end if;
  update public.guilds set notice = left(btrim(coalesce(p_text,'')), 200) where id = m.guild_id;
  return public.guild_state();
end; $$;

/* ------------------------------ LÔI ĐÀI ------------------------------ */
create or replace function public.arena_challenge(p_target uuid)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare me uuid := auth.uid(); a record; d record; cid bigint;
begin
  perform public._need_real(); perform public._require_clean();
  if p_target is null or p_target = me then raise exception 'Không thể tự khiêu chiến mình'; end if;
  select * into a from public._wo_me(me);
  begin select * into d from public._wo_me(p_target); exception when others then raise exception 'Đối thủ chưa nhập đạo'; end;
  update public.arena_challenges set status = 'expired', resolved_at = now()
    where status = 'pending' and created_at < now() - interval '90 seconds' and (challenger = me or target = me or challenger = p_target or target = p_target);
  if exists (select 1 from public.arena_challenges where challenger = me and target = p_target and status = 'pending') then
    raise exception 'Đã gửi chiến thư — chờ đối phương trả lời'; end if;
  if (select count(*) from public.arena_challenges where challenger = me and status = 'pending') >= 3 then
    raise exception 'Ngươi đang chờ quá nhiều chiến thư'; end if;
  insert into public.arena_challenges(challenger, target, c_name, t_name) values (me, p_target, a.nm, d.nm) returning id into cid;
  return jsonb_build_object('id', cid);
end; $$;

create or replace function public.arena_cancel(p_id bigint)
returns void language plpgsql security definer set search_path to 'public' as $$
begin
  update public.arena_challenges set status = 'cancelled', resolved_at = now() where id = p_id and challenger = auth.uid() and status = 'pending';
end; $$;

create or replace function public.arena_respond(p_id bigint, p_accept boolean)
returns jsonb language plpgsql security definer set search_path to 'public' as $$
declare
  me uuid := auth.uid(); c public.arena_challenges; a record; d record; pa jsonb; pd jsonb;
  ha int; hd int; amx int; dmx int; rnd int := 0; lg jsonb := '[]'::jsonb; first_a boolean; dmg int; cr boolean; won boolean;
  sa public.arena_stats; sd public.arena_stats; ea numeric; delta int; used int; reward int := 0; rev int; res jsonb;
begin
  perform public._need_real(); perform public._require_clean();
  select * into c from public.arena_challenges where id = p_id for update;
  if not found or c.target <> me then raise exception 'Chiến thư không tồn tại'; end if;
  if c.status <> 'pending' then raise exception 'Chiến thư đã hết hiệu lực'; end if;
  if c.created_at < now() - interval '90 seconds' then
    update public.arena_challenges set status = 'expired', resolved_at = now() where id = p_id;
    raise exception 'Chiến thư đã quá hạn'; end if;
  if not coalesce(p_accept, false) then
    update public.arena_challenges set status = 'declined', resolved_at = now() where id = p_id;
    return jsonb_build_object('declined', true);
  end if;
  select count(*) into used from public.arena_challenges where status = 'done' and (challenger = me or target = me) and resolved_at > now() - interval '1 day';
  if used >= 30 then raise exception 'Hôm nay ngươi đã lên lôi đài đủ ba mươi trận'; end if;
  select * into a from public._wo_me(c.challenger);
  select * into d from public._wo_me(c.target);
  if coalesce((a.st->>'dead')::boolean,false) or coalesce((d.st->>'dead')::boolean,false) then raise exception 'Một bên đã tọa hóa'; end if;
  pa := public._online_power(a.st); pd := public._online_power(d.st);
  amx := greatest(1,(pa->>'hp')::int); dmx := greatest(1,(pd->>'hp')::int); ha := amx; hd := dmx;
  first_a := (pa->>'spd')::int >= (pd->>'spd')::int;
  while rnd < 40 and ha > 0 and hd > 0 loop
    rnd := rnd + 1;
    if first_a then
      cr := random()*100 < (pa->>'crit')::int; dmg := greatest(1, round((pa->>'atk')::int*(0.85+random()*0.3) - (pd->>'def')::int*0.5)::int); if cr then dmg := round(dmg*1.6)::int; end if;
      hd := hd - dmg; lg := lg || jsonb_build_object('s','a','d',dmg,'c',cr,'h',greatest(hd,0));
      exit when hd <= 0;
      cr := random()*100 < (pd->>'crit')::int; dmg := greatest(1, round((pd->>'atk')::int*(0.85+random()*0.3) - (pa->>'def')::int*0.5)::int); if cr then dmg := round(dmg*1.6)::int; end if;
      ha := ha - dmg; lg := lg || jsonb_build_object('s','d','d',dmg,'c',cr,'h',greatest(ha,0));
    else
      cr := random()*100 < (pd->>'crit')::int; dmg := greatest(1, round((pd->>'atk')::int*(0.85+random()*0.3) - (pa->>'def')::int*0.5)::int); if cr then dmg := round(dmg*1.6)::int; end if;
      ha := ha - dmg; lg := lg || jsonb_build_object('s','d','d',dmg,'c',cr,'h',greatest(ha,0));
      exit when ha <= 0;
      cr := random()*100 < (pa->>'crit')::int; dmg := greatest(1, round((pa->>'atk')::int*(0.85+random()*0.3) - (pd->>'def')::int*0.5)::int); if cr then dmg := round(dmg*1.6)::int; end if;
      hd := hd - dmg; lg := lg || jsonb_build_object('s','a','d',dmg,'c',cr,'h',greatest(hd,0));
    end if;
  end loop;
  if hd <= 0 then won := true; elsif ha <= 0 then won := false; else won := (ha::float/amx) >= (hd::float/dmx); end if;

  insert into public.arena_stats(user_id, name, realm_idx) values (c.challenger, a.nm, a.realm) on conflict (user_id) do update set name = excluded.name, realm_idx = excluded.realm_idx;
  insert into public.arena_stats(user_id, name, realm_idx) values (c.target, d.nm, d.realm) on conflict (user_id) do update set name = excluded.name, realm_idx = excluded.realm_idx;
  select * into sa from public.arena_stats where user_id = c.challenger;
  select * into sd from public.arena_stats where user_id = c.target;
  ea := 1 / (1 + power(10, (sd.points - sa.points) / 400.0));
  delta := greatest(1, round(32 * (case when won then 1 - ea else ea end))::int);
  if won then
    update public.arena_stats set points = points + delta, wins = wins + 1, updated_at = now() where user_id = c.challenger;
    update public.arena_stats set points = greatest(0, points - delta), losses = losses + 1, updated_at = now() where user_id = c.target;
  else
    update public.arena_stats set points = greatest(0, points - delta), losses = losses + 1, updated_at = now() where user_id = c.challenger;
    update public.arena_stats set points = points + delta, wins = wins + 1, updated_at = now() where user_id = c.target;
  end if;
  -- thưởng linh thạch cho bên thắng, mỗi cặp đối thủ chỉ tính một lần mỗi giờ
  if not exists (select 1 from public.arena_challenges where status = 'done' and resolved_at > now() - interval '1 hour'
      and ((challenger = c.challenger and target = c.target) or (challenger = c.target and target = c.challenger))) then
    reward := 40 * (1 + (case when won then a.realm else d.realm end));
    begin rev := public._inv_add(case when won then c.challenger else c.target end, array['state','spiritStones'], reward);
    exception when others then reward := 0; end;
  end if;
  res := jsonb_build_object('won', won, 'log', lg, 'aHp', amx, 'dHp', dmx, 'rounds', rnd, 'delta', delta, 'reward', reward,
    'aName', a.nm, 'dName', d.nm, 'aRealm', a.realm, 'dRealm', d.realm);
  update public.arena_challenges set status = 'done', result = res, resolved_at = now() where id = p_id;
  return res;
end; $$;

revoke all on function public._wo_me(uuid) from public, anon, authenticated;
revoke execute on function public.chat_send(text,text), public.guild_state(), public.guild_list(), public.guild_create(text,text),
  public.guild_join(bigint), public.guild_leave(), public.guild_kick(uuid), public.guild_set_role(uuid,text), public.guild_donate(integer),
  public.guild_notice(text), public.arena_challenge(uuid), public.arena_cancel(bigint), public.arena_respond(bigint,boolean) from public, anon;
grant execute on function public.chat_send(text,text), public.guild_state(), public.guild_list(), public.guild_create(text,text),
  public.guild_join(bigint), public.guild_leave(), public.guild_kick(uuid), public.guild_set_role(uuid,text), public.guild_donate(integer),
  public.guild_notice(text), public.arena_challenge(uuid), public.arena_cancel(bigint), public.arena_respond(bigint,boolean) to authenticated;

do $$ begin
  begin alter publication supabase_realtime add table public.world_chat; exception when duplicate_object then null; end;
  begin alter publication supabase_realtime add table public.arena_challenges; exception when duplicate_object then null; end;
end $$;
