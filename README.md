# דאשבורד שירות לקוחות

דאשבורד דמה שמציג פניות של לקוחות: מי פנה, מתי, באיזה נושא, ובאיזה שלב הטיפול נמצא.

## 🔗 צפייה בדשבורד
**https://tamar-shtein.github.io/customer-service-dashboard/**

## מה יש בדשבורד
- **מדדים:** סך כל הפניות, פניות פתוחות, שיעור הפניות שנסגרו, וסוג הפנייה הנפוץ ביותר.
- **גרף עוגה:** התפלגות הפניות לפי סטטוס טיפול.
- **גרף עמודות:** מספר הפניות לפי סוג פנייה.
- **טבלה:** כל 30 הפניות, ממוינות מהחדשה לישנה, עם חיפוש לפי שם וסינון לפי סטטוס וסוג.

## מאיפה מגיעים הנתונים: Airtable
הנתונים כבר לא נוצרים בתוך הקובץ. המקור שלהם הוא טבלת **Tickets** ב-Airtable:

```
Airtable (טבלת Tickets)
   │  GitHub Actions, כל שעה: scripts/fetch_airtable.py
   │  (קורא את ה-API של Airtable עם הטוקן מ-GitHub Secrets)
   ▼
data/tickets.json
   │  הדאשבורד טוען את הקובץ
   ▼
index.html  ←  מציג "מקור הנתונים: Airtable · סונכרן לאחרונה …"
```

**למה לא לקרוא מ-Airtable ישירות מהדפדפן?** כי אז הטוקן היה צריך להיות בקוד של הדף, וכל מי שפותח את הדף היה רואה אותו.
הטוקן נשאר רק ב-GitHub Secrets, ו-GitHub Actions הוא היחיד שמדבר עם Airtable.

משנים פנייה ב-Airtable → אחרי הסנכרון הבא (או בלחיצה על **Run workflow**) הדאשבורד מתעדכן.

רשומה עם שדה חסר או ערך לא מוכר לא מוצגת בדאשבורד. היא נרשמת ברשימת "נדחו" עם הסיבה, כדי שאפשר יהיה לתקן אותה ב-Airtable.

## הקמה
1. **Airtable:** יוצרים base, ו[טוקן](https://airtable.com/create/tokens) עם גישה ל-base הזה בלבד.
2. **טעינה ראשונה של 30 הפניות (פעם אחת, מהמחשב):**
   ```
   cp .env.example .env      # ממלאים AIRTABLE_TOKEN ו-AIRTABLE_BASE_ID
   python scripts/seed_airtable.py
   ```
   הסקריפט יוצר את טבלת Tickets ומכניס את הפניות מ-`data/seed_tickets.json`. אפשר להריץ אותו פעמיים בלי ליצור כפילויות.
3. **GitHub:** ב-Settings → Secrets and variables → Actions:
   - **Secret** בשם `AIRTABLE_TOKEN`: טוקן נפרד, לקריאה בלבד (`data.records:read`).
   - **Variable** בשם `AIRTABLE_BASE_ID`: מזהה ה-base (מתחיל ב-`app`).
4. ב-Actions → **Sync from Airtable** → **Run workflow**. אחרי דקה ייווצר `data/tickets.json` והדאשבורד יציג את הנתונים.

## קבצים
- `index.html`: הדאשבורד. טוען את `data/tickets.json`.
- `scripts/fetch_airtable.py`: קורא את כל הפניות מ-Airtable ובודק אותן בכניסה.
- `scripts/seed_airtable.py`: הקמה חד-פעמית של הטבלה והנתונים.
- `scripts/airtable.py`: חיבור ל-API של Airtable (ספריית Python סטנדרטית בלבד).
- `.github/workflows/sync-airtable.yml`: הסנכרון האוטומטי.
- `.env.example`: תבנית למשתני הסביבה. הקובץ האמיתי `.env` לא נשמר ב-Git.
- `SPEC.md`: אפיון הפרויקט.
