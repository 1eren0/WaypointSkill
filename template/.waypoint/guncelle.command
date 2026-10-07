#!/bin/sh
# Waypoint güncelleyici. Kullanıcı çift tıklar; yapay zekâ bu dosyayı kendisi çalıştırmaz.
# Kurulum bu dosyayı çalışırken değiştirir; bu yüzden her şey tek blok olarak okunur.
{
    cd "$(dirname "$0")/.." || exit 1
    gh api repos/erenuzman/WaypointSkill/contents/install.sh -H "Accept: application/vnd.github.raw" | sh
    printf '\n%s\n' 'Bitti. Bu pencereyi kapatıp yapay zekâya "güncelledim" yaz.'
    exit
}
