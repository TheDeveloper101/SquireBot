create table player (
  uuid player_id primary key; /* An internal id for the player */
	bigint discord_id;
  varchar(255) player_name;

  check (player_name <> NULL or discord_id
  			<> NULL); /* A player is either a discord player or a dummy player */
  
  varchar(255) default_trice_name;
);

create table tournament_settings (
  uuid settings_id primary key;
	boolean make_vc not null;
  boolean make_tc not null;
  boolean trice_bot not null;
  boolean spectators_allowed not null;
  boolean spectators_can_see_hands not null;
  boolean spectators_can_chat not null;
  boolean only_registered not null;

  varchar(50) format not null;
  int match_duration check(tournament_settings.match_duration > 0) not null;
  int players check(tournament_settings.players > 0) not null;
);

create table guild (
	bigint guild_id primary key;
  varchar(255) guild_name not null; /* A cache of the guild name */
  default_settings_id references tournament_settings(settings_id) not null;
);

