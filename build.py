"""從 Google 日曆公開假日資料產生可訂閱的繁體中文行事曆。

- ancient-holidays.ics：埃及、伊拉克、印度合併，節日名稱翻成繁體中文
- taiwan-holidays.ics：台灣節慶假日

用法：python build.py [輸出資料夾]
"""
import datetime
import hashlib
import os
import re
import sys
import urllib.request
from collections import OrderedDict

ANCIENT_SOURCES = [
    ("埃及", "en.eg"),
    ("伊拉克", "en.iq"),
    ("印度", "en.indian"),
]
TAIWAN_SOURCE = "zh-tw.taiwan"
URL ="https://calendar.google.com/calendar/ical/{}%23holiday%40group.v.calendar.google.com/public/basic.ics"

# 英文名稱 -> (繁中名稱, 說明)
NAMES = {
    # 通用
    "New Year's Day": ("元旦", ""),
    "New Year's Eve": ("跨年夜", ""),
    "Labor Day": ("勞動節", ""),
    "Christmas Day": ("聖誕節", ""),
    "Christmas": ("聖誕節", ""),
    "Christmas Eve": ("平安夜", ""),
    "Good Friday": ("耶穌受難日", ""),
    "Public Holiday": ("公眾假期", "政府宣布的臨時放假日"),
    "Public Sector Holiday": ("公部門放假日", ""),
    # 伊斯蘭節日
    "Ramadan Start": ("齋戒月開始", "伊斯蘭曆 9 月首日"),
    "Eid el Fitr": ("開齋節", "齋戒月結束的慶典"),
    "Eid al-Fitr": ("開齋節", "齋戒月結束的慶典"),
    "Ramzan Id": ("開齋節", "齋戒月結束的慶典"),
    "Eid al-Adha": ("宰牲節", "又稱古爾邦節"),
    "Bakrid": ("宰牲節", "又稱古爾邦節"),
    "Eid al-Adha Public Sector Holiday": ("宰牲節公部門放假", ""),
    "Arafat Day": ("阿拉法特日", "宰牲節前一天"),
    "Islamic New Year": ("伊斯蘭新年", "伊斯蘭曆 1 月 1 日"),
    "Muharram": ("伊斯蘭新年", "伊斯蘭曆 1 月 1 日"),
    "Ashura": ("阿舒拉節", "伊斯蘭曆 1 月 10 日"),
    "Muharram/Ashura": ("阿舒拉節", "伊斯蘭曆 1 月 10 日，印度稱為穆哈蘭姆節"),
    "Prophet Mohamed's Birthday": ("先知穆罕默德誕辰", "又稱聖紀節"),
    "The Prophet's Birthday": ("先知穆罕默德誕辰", "又稱聖紀節"),
    "Milad un-Nabi": ("先知穆罕默德誕辰", "又稱聖紀節"),
    "Eid al-Ghadeer": ("加迪爾節", "什葉派節日"),
    "Arbaeen": ("阿爾巴因節", "阿舒拉節後第 40 天，什葉派節日"),
    "Jamat Ul-Vida": ("告別聚禮日", "齋戒月最後一個星期五"),
    "Hazarat Ali's Birthday": ("阿里誕辰", "伊斯蘭第四任哈里發"),
    # 埃及
    "Coptic Christmas Day": ("科普特聖誕節", ""),
    "Coptic Easter Sunday": ("科普特復活節", ""),
    "Coptic Good Friday": ("科普特耶穌受難日", ""),
    "Coptic Holy Saturday": ("科普特聖週六", ""),
    "Coptic Maundy Thursday": ("科普特濯足節", ""),
    "Nayrouz": ("科普特新年", "又稱奈魯茲節"),
    "Spring Festival": ("聞風節", "埃及傳統春天節日，在科普特復活節翌日"),
    "Flooding of the Nile": ("尼羅河氾濫節", "古埃及流傳下來的節日"),
    "Grand Egyptian Museum Opening Holiday": ("大埃及博物館開幕假期", ""),
    "January 1 Bank Holiday": ("銀行休假日", "僅銀行休假"),
    "July 1 Bank Holiday": ("銀行休假日", "僅銀行休假"),
    "Revolution Day January 25": ("一二五革命紀念日", "紀念 2011 年革命，同日也是警察節"),
    "June 30 Revolution": ("六三〇革命紀念日", "紀念 2013 年六三〇革命"),
    "Revolution Day July 23": ("七二三革命紀念日", "紀念 1952 年七月革命"),
    "Sinai Liberation Day": ("西奈解放日", "紀念 1982 年收回西奈半島"),
    "Armed Forces Day": ("武裝部隊日", "紀念 1973 年十月戰爭"),
    # 伊拉克
    "Army Day": ("建軍節", "伊拉克陸軍建軍紀念日"),
    "Nowruz": ("諾魯茲節", "波斯新年"),
    "The Halabja Massacre": ("哈拉布賈慘案紀念日", "紀念 1988 年哈拉布賈化學武器攻擊"),
    "Public Mourning Day": ("全國哀悼日", ""),
    "Football World Cup Qualification Holiday": ("世界盃資格賽假期", ""),
    "Parliamentary Elections Holiday": ("國會選舉假期", ""),
    "Post Election Holiday": ("選後假期", ""),
    # 印度
    "Republic Day": ("共和國日", "紀念 1950 年憲法生效"),
    "Independence Day": ("獨立紀念日", "紀念 1947 年獨立"),
    "Mahatma Gandhi Jayanti": ("甘地誕辰紀念日", ""),
    "Ambedkar Jayanti": ("安貝德卡誕辰紀念日", "印度憲法之父"),
    "Birthday of Rabindranath": ("泰戈爾誕辰", ""),
    "Diwali/Deepavali": ("排燈節", "印度教燈節"),
    "Naraka Chaturdasi": ("小排燈節", "排燈節前一天"),
    "Govardhan Puja": ("牛增山節", "排燈節翌日"),
    "Bhai Duj": ("兄弟節", "排燈節期間，姊妹為兄弟祈福"),
    "Raksha Bandhan": ("兄妹節", "姊妹為兄弟繫上護身繩"),
    "Holi": ("灑紅節", "又稱侯麗節、色彩節"),
    "Holika Dahana": ("霍利卡焚燒夜", "灑紅節前夕"),
    "Dolyatra": ("多爾節", "孟加拉地區的灑紅節"),
    "Dussehra": ("十勝節", "慶祝羅摩戰勝魔王"),
    "First Day of Sharad Navratri": ("九夜節首日", ""),
    "First Day of Durga Puja Festivities": ("杜爾迦節首日", ""),
    "Maha Saptami": ("杜爾迦節第七日", ""),
    "Maha Ashtami": ("杜爾迦節第八日", ""),
    "Maha Navami": ("杜爾迦節第九日", ""),
    "Ganesh Chaturthi": ("象神節", "象頭神甘尼許誕辰"),
    "Vinayaka Chathurthi": ("象神節", "象頭神甘尼許誕辰"),
    "Janmashtami": ("黑天誕辰節", "克里希納誕辰"),
    "Janmashtami (Smarta)": ("黑天誕辰節", "克里希納誕辰（斯馬爾塔派的日期）"),
    "Maha Shivaratri": ("濕婆節", ""),
    "Rama Navami": ("羅摩誕辰節", ""),
    "Buddha Purnima": ("佛誕節", "衛塞節"),
    "Mahavir Jayanti": ("大雄誕辰", "耆那教創始人"),
    "Guru Nanak Jayanti": ("那納克上師誕辰", "錫克教創始人"),
    "Guru Govind Singh Jayanti": ("戈賓德·辛格上師誕辰", "錫克教第十代上師"),
    "Guru Ravidas Jayanti": ("拉維達斯上師誕辰", ""),
    "Guru Tegh Bahadur's Martyrdom Day": ("德格·巴哈杜爾上師殉道日", "錫克教第九代上師"),
    "Maharishi Dayanand Saraswati Jayanti": ("達耶難陀誕辰", "雅利安社創始人"),
    "Maharishi Valmiki Jayanti": ("蟻垤仙人誕辰", "史詩《羅摩衍那》作者"),
    "Shivaji Jayanti": ("希瓦吉誕辰", "馬拉塔帝國開國君主"),
    "Makar Sankranti": ("摩羯節", "太陽進入摩羯宮的豐收節"),
    "Pongal": ("龐格爾節", "泰米爾豐收節"),
    "Lohri": ("羅里節", "旁遮普冬季節慶"),
    "Onam": ("歐南節", "喀拉拉豐收節"),
    "Vasant Panchami": ("春五節", "敬拜辯才天女"),
    "Karaka Chaturthi": ("卡瓦喬特節", "已婚婦女為丈夫齋戒祈福"),
    "Chhat Puja (Pratihar Sashthi/Surya Sashthi)": ("恰特節", "敬拜太陽神"),
    "Rath Yatra": ("戰車節", "普里的賈格納特神戰車遊行"),
    "Parsi New Year": ("帕西新年", "祆教徒新年"),
    "Chaitra Sukhladi": ("印度教陰曆新年", ""),
    "Gudi Padwa": ("古迪帕德瓦節", "馬拉地新年"),
    "Ugadi": ("烏加迪節", "泰盧固、卡納達新年"),
    "Cheti Chand": ("切蒂昌德節", "信德新年"),
    "Vaisakhi": ("拜薩基節", "旁遮普豐收節、錫克教新年"),
    "Vaisakhadi (Bengal)": ("孟加拉新年", ""),
    "Bahag Bihu (Assam)": ("比胡節", "阿薩姆新年"),
    "Vishu": ("維舒節", "喀拉拉新年"),
    "Mesadi": ("太陽曆新年", ""),
}

# Google 台灣繁中資料的誤譯，例如 2027 年的「補假」被寫成「厂礼拜」
TAIWAN_FIXES = {"厂礼拜": "補假"}

# Google 說明欄第一行 -> 假日類型（英文來源與台灣的繁中來源）
KINDS = {
    "Public holiday": "國定假日",
    "Observance": "節慶（不放假）",
    "國定假日": "國定假日",
    "假日節慶": "節慶（不放假）",
}


def translate(name):
    """回傳 (繁中名稱, 說明, 是否暫定, 是否已翻譯)。"""
    tentative = name.endswith(" (tentative)")
    if tentative:
        name = name[: -len(" (tentative)")]
    if name in NAMES:
        return (*NAMES[name], tentative, True)
    m = re.fullmatch(r"Day off for (.+)", name)
    if m and m.group(1) in NAMES:
        zh, note = NAMES[m.group(1)]
        return zh + "補假", note, tentative, True
    m = re.fullmatch(r"(.+) [Hh]oliday", name)
    if m and m.group(1) in NAMES:
        zh, note = NAMES[m.group(1)]
        return zh + "假期", note, tentative, True
    return name, "", tentative, False


def parse(text):
    text = re.sub(r"\r?\n[ \t]", "", text.replace("\r\n", "\n"))
    for block in text.split("BEGIN:VEVENT")[1:]:
        fields = {}
        for line in block.split("END:VEVENT")[0].strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                fields[key.split(";")[0]] = value
        yield fields


def unescape(value):
    return re.sub(r"\\([\\;,nN])", lambda m: "\n" if m.group(1) in "nN" else m.group(1), value)


def escape(value):
    return value.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    """依 RFC 5545 每行最多 75 bytes，不切斷 UTF-8 字元。"""
    out, cur, size = [], "", 0
    for ch in line:
        n = len(ch.encode("utf-8"))
        if size + n > (75 if not out else 74):
            out.append(cur)
            cur, size = "", 0
        cur += ch
        size += n
    out.append(cur)
    return "\r\n ".join(out)


def fetch(cal_id):
    with urllib.request.urlopen(URL.format(cal_id), timeout=60) as resp:
        events = list(parse(resp.read().decode("utf-8")))
    if not events:
        raise SystemExit(f"{cal_id} 的來源沒有任何活動，停止輸出")
    return events


def kind_of(ev):
    return KINDS.get(unescape(ev.get("DESCRIPTION", "")).split("\n")[0], "")


def write_calendar(path, name, caldesc, events):
    """events 為 (開始, 結束, 標題, 說明, UID 依據) 的清單。"""
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//ancient-holidays//ZH-TW",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:" + escape(name),
        "X-WR-CALDESC:" + escape(caldesc),
        "REFRESH-INTERVAL;VALUE=DURATION:P1D",
        "X-PUBLISHED-TTL:P1D",
    ]
    for start, end, title, desc, uid_key in sorted(events):
        uid = hashlib.sha1(uid_key.encode("utf-8")).hexdigest()[:20]
        lines += [
            "BEGIN:VEVENT",
            f"UID:{uid}@ancient-holidays",
            f"DTSTAMP:{stamp}",
            f"DTSTART;VALUE=DATE:{start}",
            f"DTEND;VALUE=DATE:{end}",
            "SUMMARY:" + escape(title),
            "DESCRIPTION:" + escape(desc),
            "TRANSP:TRANSPARENT",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(fold(l) for l in lines) + "\r\n")
    print(f"已輸出 {path}：{len(events)} 個活動")


def build_ancient(path):
    merged = OrderedDict()
    untranslated = set()
    for country, cal_id in ANCIENT_SOURCES:
        for ev in fetch(cal_id):
            src = unescape(ev["SUMMARY"])
            zh, note, tentative, ok = translate(src)
            if not ok:
                untranslated.add(src)
            key = (ev["DTSTART"], ev["DTEND"], zh)
            item = merged.setdefault(key, {"countries": OrderedDict(), "notes": [], "src": [], "tentative": False})
            item["countries"].setdefault(country, kind_of(ev))
            if note and note not in item["notes"]:
                item["notes"].append(note)
            if src not in item["src"]:
                item["src"].append(src)
            item["tentative"] |= tentative

    events = []
    for (start, end, zh), item in merged.items():
        countries = "、".join(item["countries"])
        title = f"{zh}（{countries}{'，暫定' if item['tentative'] else ''}）"
        desc = [f"{c}：{k}" if k else c for c, k in item["countries"].items()]
        desc += item["notes"]
        if item["tentative"]:
            desc.append("日期為暫定，可能變動")
        desc.append("英文名稱：" + " / ".join(s.replace(" (tentative)", "") for s in item["src"]))
        events.append((start, end, title, "\n".join(desc), f"{start}|{zh}"))
    write_calendar(
        path,
        "古文明國家節日",
        "埃及、伊拉克、印度的國定假日與節慶（繁體中文）。資料來源：Google 日曆公開假日資料。",
        events,
    )
    if untranslated:
        print("尚未翻譯的名稱（保留英文）：" + " | ".join(sorted(untranslated)))


def build_taiwan(path):
    # 來源已是繁體中文，只修正誤譯，並把說明欄換成假日類型（去掉 Google 的設定提示）
    events = []
    for ev in fetch(TAIWAN_SOURCE):
        title = unescape(ev["SUMMARY"])
        for wrong, right in TAIWAN_FIXES.items():
            title = title.replace(wrong, right)
        desc = "補行上班日" if "補班" in title else kind_of(ev)
        events.append((ev["DTSTART"], ev["DTEND"], title, desc, f"tw|{ev['DTSTART']}|{title}"))
    write_calendar(
        path,
        "台灣節慶假日",
        "台灣的國定假日與節慶。資料來源：Google 日曆公開假日資料。",
        events,
    )


def main(out_dir):
    build_ancient(os.path.join(out_dir, "ancient-holidays.ics"))
    build_taiwan(os.path.join(out_dir, "taiwan-holidays.ics"))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
