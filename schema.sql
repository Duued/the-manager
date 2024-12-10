CREATE DATABASE manager;

CREATE TABLE users(
    id BIGINT,
    banned BOOL,
    PRIMARY KEY(id)
);

CREATE TABLE globaltag(
    name TEXT,
    content TEXT,
    ownerid BIGINT,
    locked BOOL,
    PRIMARY KEY(name)
);

CREATE TABLE guildmanager(
    id BIGINT,
    banned BOOL,
    PRIMARY KEY(id)
)

CREATE TABLE anonymous(
    guildid BIGINT,
    channelid BIGINT
    PRIMARY KEY(channelid)
)

CREATE TABLE autoroles(
    roleid BIGINT,
    guildid BIGINT,
    PRIMARY KEY(roleid)
)

CREATE TABLE beta(
    guildid BIGINT,
    active BOOL,
    PRIMARY KEY(guildid)
)

CREATE TABLE economy(
    user_id BIGINT,
    cash BIGINT,
    PRIMARY KEY(user_id)
)

CREATE TABLE report(
    id INT,
    author BIGINT,
    url TEXT,
    reason TEXT,
    PRIMARY KEY(id)
)

CREATE TABLE reports(
    destination BIGINT,
    PRIMARY KEY(destination)
)

CREATE TABLE tickets(
    ticketno INT,
    owner BIGINT, 
    threadid BIGINT,
    open BOOL,
    PRIMARY KEY(ticketno)
)

CREATE TABLE userembeds(
    owner BIGINT,
    name TEXT NOT NULL,
    userembedno INT NOT NULL,
    content JSONB NOT NULL
)

CREATE TABLE calls(
    id INT,
    server_one_id BIGINT,
    channel_one_id BIGINT,
    server_two_id BIGINT,
    channel_two_id BIGINT,
    PRIMARY KEY(id)
)

CREATE TABLE messages(
    id BIGINT,
    call_id INT,
    content TEXT,
    author_id BIGINT,
    channel_id BIGINT,
    guild_id BIGINT,
    PRIMARY KEY(id)
)

CREATE TABLE guildconfig(
    guild_id BIGINT,
    global_bans_enabled BOOL,
    auto_sync_global_Bans BOOL,
    PRIMARY KEY(guild_id)
)

CREATE TABLE tasks(
    name TEXT,
    channel_id BIGINT,
    message_id BIGINT,
    owner_id BIGINT,
    time TIMESTAMP
)

CREATE TABLE self_promo_tasks(
    user_id BIGINT,
    time TIMESTAMP,
    PRIMARY KEY(user_id)
)

CREATE TABLE global_ban_report(
    user_id BIGINT,
    reported_by BIGINT,
    reason TEXT,
    PRIMARY KEY(user_id)
)

CREATE TABLE global_bans(
    user_id BIGINT,
    reported_by BIGINT,
    reason TEXT,
    approved_by BIGINT,
    PRIMARY KEY(user_id)
)

CREATE TABLE command_logs(
    user_id BIGINT,
    channel_id BIGINT,
    guild_id BIGINT,
    command TEXT,
    timestamp TIMESTAMP,
    type TEXT
)

CREATE TABLE call_config(
    guild_id BIGINT PRIMARY KEY,
    swears_allowed BOOL DEFAULT TRUE,
    adult_allowed BOOL DEFAULT FALSE
)