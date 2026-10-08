#!/bin/sh
# Waypoint güncelleyici. Kullanıcı çift tıklar; yapay zekâ bu dosyayı kendisi çalıştırmaz.
# Kurulum bu dosyayı çalışırken değiştirir; bu yüzden her şey tek blok olarak okunur.
{
    cd "$(dirname "$0")/.." || exit 1
    curl -fsSL https://raw.githubusercontent.com/erenuzman/WaypointSkill/main/install.sh | sh
    printf '\n%s\n' 'Bitti. Bu pencereyi kapatıp yapay zekâya "güncelledim" yaz.'
    exit
}
