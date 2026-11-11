#!/bin/sh
# Yeni müştəri qovluğu: sh new_client.sh <qovluq-adi> "<Görünən ad>"
# Nümunə: sh new_client.sh dental-smile "Dental Smile"
set -e
root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)/instagram-clients"
slug="$1"; name="${2:-$1}"
[ -n "$slug" ] || { echo "usage: new_client.sh <slug> \"<Ad>\""; exit 1; }
d="$root/$slug"; [ -e "$d" ] && { echo "artıq var: $d"; exit 1; }
mkdir -p "$d"; cp "$root/_template/"* "$d/"
sed -i "1s/.*/# $name · Brend qaydaları/" "$d/brand.md"
printf '# %s · Kontekst və rəylər\n\n## Status\n- Başlanğıc: %s\n\n## Rəylər (tarix · iş · rəy)\n\n## Paylaşılanlar\n\n## Növbəti addımlar\n' "$name" "$(date +%F)" > "$d/context.md"
echo "$d"; ls "$d"
