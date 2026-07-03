#!/data/data/com.termux/files/usr/bin/bash
set -e

pkg update -y
pkg install python ffmpeg termux-api git -y
pip install -e .

echo "PrestesOS instalado. Execute: prestes"
