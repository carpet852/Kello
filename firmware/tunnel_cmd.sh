#!/bin/sh

#set -x

if [ -n "$KELLO_IP" ]; then
  IP=$KELLO_IP
else
  IP=Kello_E05FBC.local
fi

if [ -n "$KELLO_SERIAL" ]; then
  CMD_SINK="tee $KELLO_SERIAL"
else
  CMD_SINK="nc $IP 4444"
fi


# spotify blobs (depends on user/profile ?)
# Fearless Motivation, Nick playlist
# 0045spotify:5000000068e0df89b04a53bf6c4f647cf5631391026e69636b2e72616d696c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000:Spotify 68e0df89b04a

util_getwifiip(){
  ip addr show dev wlp4s0 |sed '/inet /!d; s/.*inet //; s/\/.*//'
}

raw() {
  ( printf "$1"; sleep 1; ) | $CMD_SINK
}

hello(){
  ( printf "\n0c00\r"; sleep 1; ) | $CMD_SINK
#( echo -n 02; echo -n "CST6CDT,M3.2.0/2:00:00,M11.1.0/2:00:00\r"; ) | $CMD_SINK
}


set_global_flags() {
  GLOBAL_FLAGS=0
  if [ $# -ge 1 ]; then
    GLOBAL_FLAGS=$((GLOBAL_FLAGS + 1))
    shift
  fi
  if [ $# -ge 1 ]; then
    GLOBAL_FLAGS=$((GLOBAL_FLAGS + 2))
    shift
  fi
  printf "\n0p02%02x\r" $GLOBAL_FLAGS | $CMD_SINK
}

get_global_flags() {
  printf "\n0g02\r" | $CMD_SINK
}

set_12_24h_display() {
  if [ -z "$1" ]; then
    LOCALE_FLAG="01"
  elif [ "$1" -ge 1 ]; then
    LOCALE_FLAG="01"
  else
    LOCALE_FLAG="00"
  fi
  printf "\n0p01%02x\r" $LOCALE_FLAG | $CMD_SINK
}

time_display_refresh_allow() {
  if [ -z "$1" ]; then
    ALLOW=1
  elif [ "$1" -ge 1 ]; then
    ALLOW=1
  else
    ALLOW=0
  fi
  if [ $ALLOW -eq 1 ]; then
    printf "\n0p19\r" | $CMD_SINK
  else
    printf "\n0d19\r" | $CMD_SINK
  fi
}


factory_reset() {
  printf "\n0c04\r" | $CMD_SINK
}


upgrade() {
  if [ "$1" = usb ]; then
    URL=usb
  elif [ "$1" = "auto" ]; then
    SERVER_IP=$(util_getwifiip)
    URL="http\:\/\/$SERVER_IP\:8000\/kello.xml"
  else
    URL=""
  fi
  printf "\n0c05$URL\r" | $CMD_SINK
}

key(){
  ( printf "\n0p08%s\r" "$1"; ) | $CMD_SINK
}

event(){
  ( printf "\n0e08%s\r" "$1"; ) | $CMD_SINK
}

key_bigbutton(){
  ( printf "\n0p08big_button\r"; ) | $CMD_SINK
}

key_action(){
  ( printf "\n0p08action\r"; ) | $CMD_SINK
}


screen_auto_get() {
  ( printf "\n0g06\r"; sleep 1; ) | $CMD_SINK; echo
}
screen_auto_set() {
  ( printf "\n0p06%d\r" 0; sleep 1; ) | $CMD_SINK; echo
}
screen_auto_clear() {
  ( printf "\n0p06%d\r" 1; sleep 1; ) | $CMD_SINK; echo
}
screen_brightness_get() {
  ( printf "\n0g07\r"; sleep 1; ) | $CMD_SINK; echo
}
screen_brightness_set() {
  ( printf "\n0p07%x\r" $1; sleep 1; ) | $CMD_SINK; echo
}
screen_brightness_als() {
  ( printf "\n0a07%x\r" $1; sleep 1; ) | $CMD_SINK; echo
}

key_action(){
  ( printf "\n0p08action\r"; ) | $CMD_SINK
}



screen_user_clear() {
  ( printf "\n0c09\r" "$1"; sleep 1; ) | $CMD_SINK; echo
}

screen_user_text() {
  ( printf "\n0t09%s\r" "$1"; sleep 1; ) | $CMD_SINK; echo
}

screen_user_pix() {
  ( printf "\n0b09%x:%x:1:1:1\r" "$1" "$2"; sleep 1; ) | $CMD_SINK; echo
}

screen_user_data() {
  ( printf "\n0b090:0:%x:%x:%s\r" 24 8 "$1"; sleep 1; ) | $CMD_SINK; echo
}


screen_user_fill() {
  ( printf "\n0b090:0:18:8:FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF\r" "$1" "$2"; sleep 1; ) | $CMD_SINK; echo
}

screen_user_heart() {
  ( printf "\n0b09%x:%x:8:7:66FFFFFF7E3C18\r" "$1" "$2"; sleep 1; ) | $CMD_SINK; echo
}

screen_user_show() {
  ( printf "\n0p09\r" "$1"; sleep 1; ) | $CMD_SINK; echo
}

screen_user_remove() {
  ( printf "\n0d09\r" "$1"; sleep 1; ) | $CMD_SINK; echo
}


put_ntp() {
  printf "\n0s10\r" $s $N | $CMD_SINK
}

put_date() {
  if [ -n "$1" ]; then
    eval $(date -d "$1" "+s=%s N=%N"|sed 's/=0/=/g')
  else
    eval $(date "+s=%s N=%N"|sed 's/=0/=/g')
  fi
  if [ "$N"  = "N" ]; then N=0; fi # on mac
  printf "\n0p10%x:%x\r" $s $N | $CMD_SINK
#  ( printf "\n0p10\r"; date +%s:%N; ) | $CMD_SINK
#  ( echo -n 011:001000000|tr -d '\r'; ) | $CMD_SINK
}

put_timezone(){
  DATEZ=$(date +%z)
  if [ -n "DATEZ" ]; then
    eval $(echo $DATEZ | sed 's/\(.\)\(..\)\(..\)/S=\1 H=\2 M=\3/'|sed 's/=0/=/g')
    SECS=$[ $H * 3600 + $M*60 ]
    put_timezone_s $SECS
  else
    put_timezonehk
  fi
}

put_timezonehk(){
  # 28800 = 0x7080 = 8 * 60 * 60 hex, 8h, HKT
  ( printf "\n0p11%x\r" 28800; ) | $CMD_SINK
}

put_timezonefr(){
  # standard time, change in mars, summer time
  NEXT_CHANGE=$(TZ=Europe/Paris date -d "2016/03/27 03:00:00" +%s)
  ( printf "\n0p11%x:%x:%x\r" $(expr 1 "*" 3600) $NEXT_CHANGE $(expr 2 "*" 3600); ) | $CMD_SINK
}

put_timezone_s(){
  SECS=$1
  HEXSECS=$(printf %08x $SECS | tail -c 8)
  ( printf "\n0p11%s\r" $HEXSECS; ) | $CMD_SINK
}

get_alarms() {
  ( printf "\n0g20\r"; sleep 3; ) | $CMD_SINK
}

add_alarms() {
  ( printf "\n0a201:%x:%x:0:%x:0:0:0:0:Flow:deezer\:\/\/\/user\/me\/flow\r"; sleep 1; ) | $CMD_SINK
}

delete_alarm() {
  if [ $# -ge 1 ]; then
    alarm_id=$1
  else
    alarm_id=0
  fi
  ( printf "\n0d200\r"; sleep 1; ) | $CMD_SINK
}

delete_alarm() {
  ( printf "\n0d20%d\r" $1; sleep 1; ) | $CMD_SINK
}

put_alarm0_soon_errparse() {
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  ( printf "\n0p210:3:%x:%x:7f:50:0:0:Fearless Motivation:spotify\:\/\/\/blob\/5000000068e0df89b04a53bf6c4f647cf5631391026e69636b2e72616d696c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000\r" $H $((M+1)); sleep 1; ) | $CMD_SINK
}

put_alarm0_soon_spotify() {
  if [ $# -ge 1 ]; then
    MINS=$1
  else
    MINS=1
  fi
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  MM=$((60*$H+$M+$MINS))
  H=$((MM/60))
  M=$((MM%60))
( printf "\n0p210:3:%x:%x:7f:50:0:0:0:0:Fearless Motivation:spotify\:\/\/\/blob\/5000000068e0df89b04a53bf6c4f647cf5631391026e69636b2e72616d696c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000\r" $H $M; sleep 1; ) | $CMD_SINK
}

put_alarm0_soon_target_spotify() {
  eval $(date "+H=%H M=%M E=%s"|sed 's/=0/=/g')
  ( printf "\n0p210:b:%x:%x:7f:50:10:0:20:%x:Fearless Motivation:spotify\:\/\/\/blob\/5000000068e0df89b04a53bf6c4f647cf5631391026e69636b2e72616d696c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000\r" $H $((M+1)) $E; sleep 1; ) | $CMD_SINK
}

put_alarm0_soon_target_spotify_pause() {
  eval $(date "+H=%H M=%M E=%s"|sed 's/=0/=/g')
  ( printf "\n0p210:a:%x:%x:7f:50:10:0:20:%x:Fearless Motivation:spotify\:\/\/\/blob\/5000000068e0df89b04a53bf6c4f647cf5631391026e69636b2e72616d696c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000\r" $H $((M+1)) $E; sleep 1; ) | $CMD_SINK
}

put_alarm0_soon_tunein() {
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  ( printf "\n0p210:3:%x:%x:7f:50:0:0:0:0:RTHK 3:tunein\:\/\/\/blob\/RTHK 3\r" $H $((M+1)); sleep 1; ) | $CMD_SINK
}

put_alarm0_soon_tunein_bfm() {
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  ( printf "\n0p210:3:%x:%x:7f:50:0:0:0:0:BFM Radio:tunein\:\/\/\/blob\/BFM Radio\r" $H $((M+1)); sleep 1; ) | $CMD_SINK
}

put_alarm0_soon_spotify_current() {
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  ( printf "\n0p210:3:%x:%x:7f:50:0:0:0:0::spotify\:\/\/\/connect\r" $H $((M+1)); sleep 1; ) | $CMD_SINK
}


put_alarm0_soon_deezer_90() {
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  ( printf "\n0p210:3:%x:%x:7f:50:0:0:0:0:90\'s:deezer\:\/\/\/user/playlist_by_name\/90's\r" $H $((M+1)); sleep 1; ) | $CMD_SINK
}

put_alarm0_soon_deezer_am() {
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  ( printf "\n0p210:3:%x:%x:7f:50:0:0:0:0:American human beeing:deezer\:\/\/\/user/playlist_by_name\/American human beeing\r" $H $((M+1)); sleep 1; ) | $CMD_SINK
}

put_alarm0_soon_deezer_loved() {
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  ( printf "\n0p210:3:%x:%x:7f:64:0:0:0:0:Loved tracks:deezer\:\/\/\/user/playlist_by_name\/Loved tracks\r" $H $((M+1)); sleep 1; ) | $CMD_SINK
}

put_alarm0_soon_deezer_flow() {
  if [ $# -ge 1 ]; then
    MINS=$1
  else
    MINS=1
  fi
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  MM=$((60*$H+$M+$MINS))
  H=$((MM/60))
  M=$((MM%60))
  ( printf "\n0p210:3:%x:%x:7f:50:0:0:0:0:Flow:deezer\:\/\/\/user\/me\/flow\r" $H $M; sleep 1; ) | $CMD_SINK
}

put_alarm0_nonrec() {
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  ( printf "\n0p210:1:%x:%x:0:%x:0:0:0:0:Flow:deezer\:\/\/\/user\/me\/flow\r" $H $((M+1)) 80; sleep 1; ) | $CMD_SINK
}

put_alarm0_soon_local() {
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  ( printf "\n0p210:3:%x:%x:7f:50:0:0:0:0:Bees:local\:\/\/\/1\r" $H $((M+1)); sleep 1; ) | $CMD_SINK
}



put_alarm0_9() {
  ( printf "\n0p210:3:9:0:7f:50:0:0:0:0:Flow:deezer\:\/\/\/user\/me\/flow\r"; sleep 1; ) | $CMD_SINK
}

put_alarm0_7_disable() {
  ( printf "\n0p210:2:7:0:7f:50:0:0:0:0:Fearless Motivation:spotify\:\/\/\/blob\/5000000068e0df89b04a53bf6c4f647cf5631391026e69636b2e72616d696c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000\r"; sleep 1; ) | $CMD_SINK
}

get_alarm() {
  if [ $# -ge 1 ]; then
    alarm_id=$1
  else
    alarm_id=0
  fi
  ( printf "\n0g21%x\r" $alarm_id; sleep 1; ) | $CMD_SINK; echo
}

alarms_max() {
  ( printf "\n0m20\r"; sleep 1; ) | $CMD_SINK; echo
}
alarms_get() {
  ( printf "\n0g20\r"; sleep 1; ) | $CMD_SINK; echo
}

alarmfsm_get() {
  ( printf "\n0g22\r"; sleep 1; ) | $CMD_SINK; echo
}
alarmfsm_stop() {
  ( printf "\n0p22stop\r"; sleep 1; ) | $CMD_SINK; echo
}
alarmfsm_snooze() {
  ( printf "\n0p22snooze\r"; sleep 1; ) | $CMD_SINK; echo
}
alarmfsm_err() {
  ( printf "\n0p22snoze\r"; sleep 1; ) | $CMD_SINK; echo
}

alarmsoff_get() {
  ( printf "\n0g23\r"; sleep 1; ) | $CMD_SINK; echo
}
alarmsoff_set() {
  ( printf "\n0p231\r"; sleep 1; ) | $CMD_SINK; echo
}
alarmsoff_clear() {
  ( printf "\n0d231\r"; sleep 1; ) | $CMD_SINK; echo
}

alarmsautosilence_get() {
  ( printf "\n0g24\r"; sleep 1; ) | $CMD_SINK; echo
}
alarmsautosilence_set() {
  AUTOSILENCE_S=$1
  if [ -z "$AUTOSILENCE_S" ]; then
    AUTOSILENCE_S=100
  fi
  ( printf "\n0p24%x\r" $AUTOSILENCE_S; sleep 1; ) | $CMD_SINK; echo
}
alarmsautosilence_clear() {
  ( printf "\n0d241\r"; sleep 1; ) | $CMD_SINK; echo
}

alarmssnooze_get() {
  ( printf "\n0g25\r"; sleep 1; ) | $CMD_SINK; echo
}
alarmssnooze_set() {
  SNOOZE_S=$1
  if [ -z "$SNOOZE_S" ]; then
    SNOOZE_S=10
  fi
  ( printf "\n0p25%x\r" $SNOOZE_S; sleep 1; ) | $CMD_SINK; echo
}

sleepprog_start() {
  if [ -n "$1" ]; then
    DURATION_S=$1
  else
    DURATION_S=1800
  fi
  # http://www.deezer.com/playlist/1492154691
  ( printf "\n0p26%x:3:5a:5a:Good night:deezer\:\/\/\/user\/playlist_by_name\/Good Night, Sleep Well...\r" $DURATION_S; sleep 1; ) | $CMD_SINK; echo
}
sleepprog_startdef() {
  ( printf "\n0p26\r"; sleep 1; ) | $CMD_SINK; echo
}
sleepprog_get() {
  ( printf "\n0g26\r"; sleep 1; ) | $CMD_SINK; echo
}
sleepprog_cancel() {
  ( printf "\n0d26\r"; sleep 1; ) | $CMD_SINK; echo
}

sleepprog_sdcard() {
  ( printf "\n0p26708:3:64:64:sdcard sleep:file\:\/\/\/media\/sdb\/sleepprog.mp3\r"; sleep 1; ) | $CMD_SINK; echo
}

getyourback_get() {
  ( printf "\n0g27\r"; sleep 1; ) | $CMD_SINK; echo
}
getyourback_set() {
  ( printf "\n0p27%x\r" 0xf; sleep 1; ) | $CMD_SINK; echo
}
getyourback_clear() {
  ( printf "\n0d27\r"; sleep 1; ) | $CMD_SINK; echo
}

snoozeless_get() {
  ( printf "\n0g28\r"; sleep 1; ) | $CMD_SINK; echo
}
snoozeless_set() {
  ( printf "\n0p28%x:%x:%x:%x\r" 0xf 3 0x7f 0; sleep 1; ) | $CMD_SINK; echo
}
snoozeless_set0() {
  ( printf "\n0p280:5:7f:0\r"; sleep 1; ) | $CMD_SINK; echo
}
snoozeless_clear() {
  ( printf "\n0d28\r"; sleep 1; ) | $CMD_SINK; echo
}


bedtime_set() {
  if [ $# -ge 1 ]; then
    MINS=$1
  else
    MINS=1
  fi
  eval $(date "+H=%H M=%M"|sed 's/=0/=/g')
  MM=$((60*$H+$M+$MINS))
  H=$((MM/60))
  M=$((MM%60))
  ( printf "\n0p291:%x:%x\r" $H $M; sleep 1; ) | $CMD_SINK; echo
}
bedtime_get() {
  ( printf "\n0g29\r"; sleep 1; ) | $CMD_SINK; echo
}
bedtime_delete() {
  ( printf "\n0d29\r"; sleep 1; ) | $CMD_SINK; echo
}
bedtime_sky_display() {
  ( printf "\n0s29\r"; sleep 1; ) | $CMD_SINK; echo
}

volume_get() {
  ( printf "\n0g40\r"; sleep 1; ) | $CMD_SINK; echo
}
volume_set() {
  ( printf "\n0p40%x\r" $1; sleep 1; ) | $CMD_SINK; echo
}
volume_start() {
  VOLUME_INIT=$1
  VOLUME_TARGET=$2
  VOLUME_DURATION=$3
  ( printf "\n0c40%x:%x:%x\r" $VOLUME_INIT $VOLUME_TARGET $VOLUME_DURATION; sleep 1; ) | $CMD_SINK; echo
}
player_load_flow() {
  ( printf "\n0p41%s\r" "uri:deezer\:\/\/\/user\/me\/flow"; sleep 1; ) | $CMD_SINK; echo
}
player_load_deezer() {
  ( printf "\n0p41%s\r" "uri:deezer\:\/\/\/user\/playlist_by_name\/$1"; sleep 1; ) | $CMD_SINK; echo
}
player_load_90() {
  ( printf "\n0p41%s\r" "uri:deezer\:\/\/\/user\/playlist_by_name\/90's"; sleep 1; ) | $CMD_SINK; echo
}
player_load_loved() {
  ( printf "\n0p41%s\r" "uri:deezer\:\/\/\/user\/playlist_by_name\/Loved tracks"; sleep 1; ) | $CMD_SINK; echo
}
player_load_american() {
  ( printf "\n0p41%s\r" "uri:deezer\:\/\/\/user\/playlist_by_name\/American human beeing"; sleep 1; ) | $CMD_SINK; echo
}
player_load_spotify_invalid() {
  ( printf "\n0p41%s\r" "uri:spotify\:\/\/\/bad"; sleep 1; ) | $CMD_SINK; echo
}
player_load_spotify() {
  # todo_put_a_valid_blob_here
  # Happy Hits !
  ( printf "\n0p41%s\r" "uri:spotify\:\/\/\/blob\/50000000c847692c0eb50236899411f858cb6d580273706f746966790000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" ; sleep 1; ) | $CMD_SINK; echo
  # Nick Life Music
#  ( printf "\n0p41%s\r" "uri:spotify\:\/\/\/blob\/5000000068e0df89b04a53bf6c4f647cf5631391026e69636b2e72616d696c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" ; sleep 1; ) | $CMD_SINK; echo
}
player_load_preset1() {
  ( printf "\n0p41%s\r" "uri:spotify\:\/\/\/presets\/1" ; sleep 1; ) | $CMD_SINK; echo
}

# playlist name should be escaped
# tunnel_cmd.sh player_load "$(echo -n "deezer:///user/playlist_by_name/2013. Ca, c'est fait"|sed 's,/,\\/,g;s,:,\\:,g')"
player_load() {
  if [ -n "$1" ]; then
    URL="$1"
  else
    URL="http://52.22.49.200/files/ota/music/500kHz_right_48000_300s.mp3"
    URL="http://52.22.49.200/files/ota/music/500kHz_stereo_48000_300s.mp3"
    URL="http://52.22.49.200/files/ota/music/500kHz_left_48000_300s.mp3"
    URL="file:///media/usb/kello/500kHz_right_48000_300s.mp3"
  fi
(printf "\n0p41uri:%s\r" "$(echo $URL|sed 's,/,\\/,g;s,:,\\:,g')" ; sleep 1; ) | $CMD_SINK; echo
}

player_load_alarm() {
  # todo_put_a_valid_blob_here
  ( printf "\n0p41alarm:%d\r" $1 ; sleep 1; ) | $CMD_SINK; echo
}
player_load_fav() {
  ( printf "\n0p41%s\r" "uri:fav\:\/\/"; sleep 1; ) | $CMD_SINK; echo
}
player_load_local() {
  if [ -n "$1" ] ;then
    URL=$1
  else
    URL="1"
  fi
  ( printf "\n0p41%s\r" "uri:local\:\/\/\/$URL"; sleep 1; ) | $CMD_SINK; echo
}
player_load_tunein() {
  ( printf "\n0p41%s\r" "uri:tunein\:\/\/\/blob\/RTHK 3"; sleep 1; ) | $CMD_SINK; echo
}
player_stop() {
  ( printf "\n0d41\r" $1; sleep 1; ) | $CMD_SINK; echo
}
player_next() {
  ( printf "\n0n41\r" $1; sleep 1; ) | $CMD_SINK; echo
}
player_shuffle() {
  ( printf "\n0s41%d\r" $1; sleep 1; ) | $CMD_SINK; echo
}


player_browse_wakeuptones() {
  ( printf "\n0g42%s\r" "/wakeuptones/local"; sleep 1; ) | $CMD_SINK|sed 's/0042//'|json_pp; echo
}

player_spotify_preset_get() {
  ( printf "\n0g45spotify\r" $1; sleep 2; ) | $CMD_SINK; echo
}
player_preset_get() {
  ( printf "\n0g45\r" $1; sleep 2; ) | $CMD_SINK; echo
}

player_preset_set() {
  ( printf "\n0s45tunein\r"; sleep 2; ) | $CMD_SINK; echo
}

player_preset_set_vtuner() {
  ( printf "\n0s45vtuner:cheriefm\r"; sleep 2; ) | $CMD_SINK; echo
}

codec_factory_settings() {
  DAC_VOLUME=0x54
  if [ -n "$1" ] ;then
    DAC_VOLUME=$1
    shift
  fi
  ( printf "\n0f40%x\r" $DAC_VOLUME; sleep 2; ) | $CMD_SINK; echo

}

stats_get() {
  ( printf "\n0g50\r"; sleep 1; ) | $CMD_SINK; echo
}
stats_reset() {
  ( printf "\n0d50\r"; sleep 1; ) | $CMD_SINK; echo
}
stats_set_reset() {
  ( printf "\n0s50::::::\r"; sleep 1; ) | $CMD_SINK; echo
}
stats_set_day0() {
  ( printf "\n0s50%x,%x,%x,%x::::::\r" $((7*3600)) 2 $((7*3600 + 4*60 + 3)) $((7*3600 + 30*60)); sleep 1; ) | $CMD_SINK; echo
}
stats_set_day2() {
  ( printf "\n0s50::%x,%x,%x,%x::::\r" $((7*3600)) 2 $((7*3600 + 4*60 + 3)) $((7*3600 + 30*60)); sleep 1; ) | $CMD_SINK; echo
}

get_doublerequest() {
  ( printf "\n0g20\r\n0g211\r"; sleep 3; ) | $CMD_SINK
}

btcmd() {
  CMDIDX=$1
  ( printf "\n0\x$(printf %x $((0x30 + $CMDIDX)))03\r" '0'; sleep 3; ) | $CMD_SINK
}

debug_mode() {
  ( printf "\n0pZz\r" '0'; ) | $CMD_SINK

}
set_datehk() {
  put_timezonehk
  put_date
}

set_datefr() {
  put_timezonefr
  put_date
}

onboarding_scanresult() {
  curl http://192.168.43.1/scanresult.asp
}

onboarding_devicename() {
  curl http://192.168.43.1/devicename.asp
}

onboarding_config() {
  SSID=$1
  Passphrase=$2
  Security="NONE"
  Security="WPA-PSK"
  Devicename=""
  curl -X POST http://192.168.43.1:80/goform/HandleSACConfiguration -d "SSID=$SSID" -d "Passphrase=$Passphrase" -d "Security=$Security" -d "Devicename=$Devicename"
}

demo_ifttt_step1() {
  put_timezonehk
  TZ=Asia/Hong_Kong put_date "2016/10/10 22:00"
  ( printf "\n0p210:1:6:1e:0:5a:0:0:0:0:Flow:deezer\\:\\\/\\\/\\\/user\\\/me\\\/flow\r"; sleep 1; ) | $CMD_SINK; echo
}
demo_ifttt_step2() {
  TZ=Asia/Hong_Kong put_date "2016/10/10 22:34:50"
}

demo_ifttt_step3() {
  TZ=Asia/Hong_Kong put_date "2016/10/10 22:59:50"
}

demo_ifttt_step4() {
  TZ=Asia/Hong_Kong put_date "2016/10/11 06:17:50"
}

demo_ifttt_step5() {
  TZ=Asia/Hong_Kong put_date "2016/10/11 06:29:50"
}
maint_date() {
  if [ -z "$1" ]; then
    RAND_OFF=0
  else
    RAND_OFF=$1
  fi
  eval $(date "+Y=%Y m=%m d=%d"|sed 's/=0/=/g')
  eval $(date -d "$Y/$m/$d 16:00:00" "+s=%s N=%N"|sed 's/=0/=/g')
  if [ "$N"  = "N" ]; then N=0; fi # on mac
  printf "\n0p10%x:%x\r" $((s+4*$RAND_OFF-1)) $N | $CMD_SINK
#  ( printf "\n0p10\r"; date +%s:%N; ) | $CMD_SINK
#  ( echo -n 011:001000000|tr -d '\r'; ) | $CMD_SINK
}

test_usbcharge_gpio() {
  printf "\n0p95%x\r" $1 | $CMD_SINK
}

#  KELLO_SERIAL=/dev/ttyUSB0 ./tests/tunnel_cmd.sh test_wifi EU Tenda_A8B1A8 WPA-PSK '$unup!!!'
#  KELLO_SERIAL=/dev/ttyUSB0 ./tests/tunnel_cmd.sh test_wifi EU 天空 WPA-PSK '$unup!!!'

test_wifi() {
  if [ $# -ge 4 ]; then
    C=$1;
    shift
  else
    C="";
  fi
  printf "\n0p92%s:%s:%s:%s\r" "$C" $1 $2 $3| $CMD_SINK
}

#export BATCH_PRODUCTION=1495079353
#make factory_data && KELLO_SERIAL=/dev/ttyUSB0 DEVICE_UNIQ_ID_FILE=$(ls -1 generated/factory-tools-20170412-$BATCH_PRODUCTION/uniq_id-*.json | tail -1) ./tests/tunnel_cmd.sh flash_loader
flash_loader() {
  # raw loader. but we want to flash factory data too
  IMAGE=device/firmware/kello.1/kello_loader.bin

  if [ ! -c $KELLO_SERIAL ]; then echo "please set KELLO_SERIAL"; exit 1; fi
  if lsof $KELLO_SERIAL > /dev/null 2>&1; then echo "should have exlusive access on serial port"; exit 1; fi
  if [ -n "$DEVICE_UNIQ_ID_FILE" ]; then DEVICE_UNIQ_ID_FILE=$(readlink -f "$DEVICE_UNIQ_ID_FILE"); fi

  FACTORY_TOOLS_VERSION=20170412
  PACKAGE_NAME=factory-tools-${FACTORY_TOOLS_VERSION}-${BATCH_PRODUCTION}
  IMAGE=$(mktemp)

  ( cd $PACKAGE_NAME; \
    ../build/gen_mcu_image.py gen_loader_facdata \
    "$BATCH_PRODUCTION" gen_loader_facdata; ) > $IMAGE
  SIZE=$(stat -c %s $IMAGE)

  printf "\n0p93%x:%x\r" 0 $SIZE| $CMD_SINK
  sx $IMAGE < $KELLO_SERIAL > $KELLO_SERIAL
  rm $IMAGE
}

# keys | screen | audio | wifi | bt | als
test_fac() {
  if [ $# -ge 1 ]; then
    C=$1;
    shift
  else
    C="keys";
  fi
  printf "\n0p91%s\r" "$C" $1 $2 $3| $CMD_SINK
}

ftest() {
  if [ $1 = "4a" ]; then
    test_fac "apps=screen:screen_init=full_high_brightness:::"
  elif [ $1 = "4b" ]; then
    test_fac "apps=screen:screen_init=full_low_brightness:::"
  elif [ $1 = "4c" ]; then
    test_fac "apps=screen:screen_init=anim_row:screen_anim_row_duration=2000::"
  elif [ $1 = "4d" ]; then
    test_fac "apps=screen:screen_init=anim_column:screen_anim_column_duration=2000::"
  elif [ $1 = "5" ]; then
    test_fac "apps=als:als_led_low_threshold=5:als_led_high_threshold=12:als_show_value:"
  elif [ $1 = "6" ]; then
    test_fac "apps=wifi:wifi_mode=sta:wifi_ssid=hkmkt:wifi_passphrase=new201607gj:wifi_sta_connect_timeout=20000"
  elif [ $1 = "7" ]; then
    test_fac "apps=bt::::"
  fi

}
if [ $# -ge 1 ]; then
  "$@"
else
  put_timezone
  put_date
  alarmsautosilence_set 100
  alarmssnooze_set 10
  # activate monitoring & crash report
  set_global_flags 1 1
fi
