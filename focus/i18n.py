"""Core workflow translations. User content and technical identifiers stay unchanged."""
import streamlit as st

TEXT = """
Today|امروز|نن
Projects & board|پروژه‌ها و تختهٔ کار|پروژې او کاري تخته
Agenda|برنامهٔ کار|کاري مهالوېش
Notes|یادداشت‌ها|یادښتونه
Focus room|اتاق تمرکز|د تمرکز خونه
Activity & review|فعالیت و مرور|فعالیت او کتنه
Planning & templates|برنامه‌ریزی و نمونه‌ها|پلان او بېلګې
Reminders|یادآوری‌ها|یادونې
Settings & backup|تنظیمات و نسخهٔ پشتیبان|تنظیمات او بیک اپ
Quick capture|ثبت سریع|چټک ثبت
Quick find & create|جستجو و ایجاد سریع|چټک لټون او جوړول
WORKSPACE|محیط کار|کاري چاپېریال
YOUR SPACE|فضای شما|ستاسې ځای
Space for your best work.|فضا برای کار بهتر شما.|ستاسې د غوره کار لپاره ځای.
Inbox|کارهای تازه|نوې چارې
Next|کار بعدی|راتلونکی کار
Doing|در حال انجام|روان کار
Done|انجام‌شده|بشپړ شوی
Low|پایین|ټیټ
Medium|متوسط|منځنی
High|بالا|لوړ
None|بدون تکرار|بې تکراره
Daily|روزانه|هره ورځ
Weekly|هفته‌وار|هره اوونۍ
Weekdays|روزهای کاری دوشنبه تا جمعه|له دوشنبې تر جمعې
Selected weekdays|روزهای انتخاب‌شده|ټاکلې ورځې
Monthly|ماهانه|هره میاشت
Custom interval|فاصلهٔ دلخواه|د خوښې واټن
Off|خاموش|بند
English|انگلیسی|انګلیسي
Dari|دری|دري
Pashto|پشتو|پښتو
Task title|عنوان کار|د کار سرلیک
Project|پروژه|پروژه
Details|جزئیات|جزیات
Status|وضعیت|حالت
Priority|اولویت|لومړیتوب
Estimate · minutes|زمان تخمینی · دقیقه|اټکلی وخت · دقیقې
Due date · optional|مهلت · اختیاری|وروستۍ نېټه · اختیاري
Repeat after completion|تکرار پس از تکمیل|له بشپړېدو وروسته تکرار
Save task|ذخیرهٔ کار|کار خوندي کول
New task|کار جدید|نوی کار
New project|پروژهٔ جدید|نوې پروژه
Edit project|ویرایش پروژه|د پروژې سمون
Project name|نام پروژه|د پروژې نوم
Purpose|هدف|موخه
Save project|ذخیرهٔ پروژه|پروژه خوندي کول
Checklist|فهرست بررسی|د کتنې لړلیک
Add item|افزودن مورد|توکی زیاتول
Remove|حذف مورد|توکی لرې کول
Today's top three|سه کار مهم امروز|د نن درې مهم کارونه
Choose today's priorities|انتخاب اولویت‌های امروز|د نن لومړیتوبونه ټاکل
Choose up to three important tasks|انتخاب تا سه کار مهم|تر درې مهمو کارونو ټاکل
Save priorities|ذخیرهٔ اولویت‌ها|لومړیتوبونه خوندي کول
New note|یادداشت جدید|نوی یادښت
Note title|عنوان یادداشت|د یادښت سرلیک
Linked project|پروژهٔ مرتبط|تړلې پروژه
Tags|برچسب‌ها|نښې
Write|نوشتن|لیکل
Preview|پیش‌نمایش|مخکتنه
Version history|تاریخچهٔ نسخه‌ها|د نسخو تاریخچه
Recover drafts|بازیابی پیش‌نویس‌ها|مسودې بېرته ترلاسه کول
Use plain editor|استفاده از ویرایشگر ساده|ساده سمونګر کارول
Save note|ذخیرهٔ یادداشت|یادښت خوندي کول
Restore this version|بازیابی این نسخه|دا نسخه بېرته راوستل
Download Markdown|دریافت Markdown|Markdown ښکته کول
Make room for what matters.|برای کار مهم وقت بسازید.|مهم کار ته وخت ورکړئ.
From idea to done.|از فکر تا انجام.|له نظره تر بشپړېدو.
A place to think clearly.|جایی برای فکر روشن.|د روښانه فکر ځای.
One thing. Your full attention.|یک کار، توجه کامل شما.|یو کار، ستاسې پوره پاملرنه.
Make the week workable.|هفته را قابل اجرا بسازید.|اوونۍ عملي کړئ.
Calendar planning|برنامه‌ریزی تقویمی|د کلیزې پلان
Project templates|نمونه‌های پروژه|د پروژې بېلګې
Estimated & recorded time|زمان تخمینی و ثبت‌شده|اټکلی او ثبت شوی وخت
Task to schedule|کار برای برنامه‌ریزی|د پلان لپاره کار
Work day|روز انجام کار|د کار ورځ
Plan this task|برنامه‌ریزی این کار|دا کار پلان کړئ
Planned work|کار برنامه‌ریزی‌شده|پلان شوی کار
Deadlines|مهلت‌ها|وروستۍ نېټې
Template|نمونه|بېلګه
New project name|نام پروژهٔ جدید|د نوې پروژې نوم
Create project from template|ایجاد پروژه از نمونه|له بېلګې پروژه جوړول
Template name|نام نمونه|د بېلګې نوم
Save reusable template|ذخیرهٔ نمونهٔ قابل استفاده|د بیا کارولو بېلګه خوندي کول
Prerequisite tasks|کارهای پیش‌نیاز|مخکیني اړین کارونه
Planned work day · separate from deadline|روز انجام کار · جدا از مهلت|د کار ورځ · له وروستۍ نېټې جلا
Custom repeat interval · days|فاصلهٔ تکرار دلخواه · روز|د تکرار واټن · ورځې
Interface language|زبان برنامه|د پروګرام ژبه
Deadline and session reminders|یادآوری مهلت و جلسه|د نېټې او ناستې یادونې
Automatic backup schedule|زمان‌بندی نسخهٔ پشتیبان|د بیک اپ مهالوېش
Automatic backups to keep|تعداد نسخه‌های پشتیبان|د ساتلو بیک اپونو شمېر
Save preferences|ذخیرهٔ تنظیمات|تنظیمات خوندي کول
Appearance & routine|ظاهر و روش کار|بڼه او کاري دود
Export & backup|خروجی و نسخهٔ پشتیبان|صادرول او بیک اپ
Trash & archive|حذف‌شده‌ها و آرشیف|حذف شوي او ارشیف
About|درباره|په اړه
Password-encrypted backup|نسخهٔ پشتیبان رمزگذاری‌شده|په پاسورډ کوډ شوی بیک اپ
Create encrypted backup|ایجاد نسخهٔ رمزگذاری‌شده|کوډ شوی بیک اپ جوړول
Download encrypted backup|دریافت نسخهٔ رمزگذاری‌شده|کوډ شوی بیک اپ ښکته کول
Restore password|رمز بازیابی|د بېرته راوستلو پاسورډ
Restore backup|بازیابی نسخهٔ پشتیبان|بیک اپ بېرته راوستل
Restore a workspace|بازیابی محیط کار|کاري چاپېریال بېرته راوستل
Download verified backup|دریافت نسخهٔ پشتیبان بررسی‌شده|کتل شوی بیک اپ ښکته کول
Create automatic backup now|ایجاد نسخهٔ پشتیبان همین حالا|اوس بیک اپ جوړول
Start focusing|آغاز تمرکز|تمرکز پیل کړئ
Pause|توقف موقت|لنډ تم
Resume|ادامه|دوام
Finish & record|پایان و ثبت|پای او ثبت
Cancel|لغو|لغوه
Session intention|هدف جلسه|د ناستې موخه
Daily focus goal · minutes|هدف تمرکز روزانه · دقیقه|د ورځني تمرکز هدف · دقیقې
Duration · minutes|مدت · دقیقه|موده · دقیقې
Capture task|ثبت کار|کار ثبتول
Return to Today|بازگشت به امروز|نن ته بېرته تلل
Mark as read|علامت‌گذاری به‌عنوان خوانده‌شده|د لوستل شوي په توګه نښه کول
Search tasks and notes|جستجوی کارها و یادداشت‌ها|کارونه او یادښتونه لټول
Search notes|جستجوی یادداشت‌ها|یادښتونه لټول
Filter tasks|پالایش کارها|کارونه چاڼول
Details|جزئیات|جزیات
Move|انتقال|لېږدول
Move up|انتقال به بالا|پورته لېږدول
Move down|انتقال به پایین|ښکته لېږدول
Blocked|در انتظار پیش‌نیاز|د مخکیني کار انتظار
Monday|دوشنبه|دوشنبه
Tuesday|سه‌شنبه|سه شنبه
Wednesday|چهارشنبه|چهارشنبه
Thursday|پنج‌شنبه|پنجشنبه
Friday|جمعه|جمعه
Saturday|شنبه|شنبه
Sunday|یک‌شنبه|یکشنبه
"""
TRANSLATIONS = {parts[0]: parts[1:] for line in TEXT.strip().splitlines() if len(parts := line.split("|")) == 3}


def t(text):
    language = st.session_state.get("_language", "English")
    if language == "English" or not isinstance(text, str):
        return text
    pair = TRANSLATIONS.get(text)
    return pair[0 if language == "Dari" else 1] if pair else text
