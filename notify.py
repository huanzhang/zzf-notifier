#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
from bs4 import BeautifulSoup
from datetime import date
from datetime import datetime
import yaml
import sqlite3
import argparse
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
import logging


logger = logging.getLogger('zzf-notifier')
hdlr = logging.FileHandler('notifier.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)


CONFIG = yaml.load(file("config.yml", "r"))
CONN = sqlite3.connect(CONFIG["db_file"], detect_types=sqlite3.PARSE_COLNAMES)


def fetch_all_tzgg():
    tzgg_url = CONFIG["tzgg_url"]
    r = urllib2.urlopen(tzgg_url).read()
    soup = BeautifulSoup(r, "lxml")
    tzgg_board = soup.find("ul", {"opentype": "page"})
    return tzgg_board.find_all("li")


def parse_data_from_tzgg_html(tzgg_tag):
    link = tzgg_tag.find("a")
    span = tzgg_tag.find("span")

    title = link.contents[0].strip() if link and link.contents else None
    url = CONFIG["tzgg_host"] + link["href"].strip() if link and link.has_attr("href") else None
    publish_date = datetime.strptime(span.contents[0].strip(), "%Y-%m-%d").date() if span and span.contents else None

    return {"title": title, "url": url, "publish_date": publish_date}


def is_tzgg_date_after_target(tzgg, target_date):
    return tzgg["publish_date"] and tzgg["publish_date"] >= target_date


def find_tzgg(title, publish_date):
    cur = CONN.cursor()
    cur.execute("SELECT * FROM tzggs WHERE title = ? AND publish_date = ?", (title, publish_date))
    return cur.fetchone()


def create_tzgg(title, url, publish_date):
    cur = CONN.cursor()
    cur.execute("INSERT INTO tzggs(title, url, publish_date) values(?, ?, ?)", (title, url, publish_date))
    CONN.commit()
    return True


def send_mail(tzgg):
    fromaddr = CONFIG["smtp"]["user_name"]
    toaddr = ",".join(CONFIG["recipients"])
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = u"[自住房公告] %s %s" % (tzgg["title"], tzgg["publish_date"].strftime("%Y-%m-%d"))

    body = u"%s\n%s" % (tzgg["title"], tzgg["url"])
    msg.attach(MIMEText(body, CONFIG["smtp"]["authentication"], 'utf-8'))

    server = smtplib.SMTP(CONFIG["smtp"]["address"], CONFIG["smtp"]["port"])
    if CONFIG["smtp"]["ssl"]:
        server.starttls()
    server.login(fromaddr, CONFIG["smtp"]["password"])
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()


def main():
    parser = argparse.ArgumentParser(description='Notify new zzf news')
    parser.add_argument('--init', dest='initialized', action='store_true',
                                  default=False,
                                  help='initialize from the beginning')
    args = parser.parse_args()
    fetch_date = date.today()
    if args.initialized:
        fetch_date = date(2016, 1, 1)

    logger.info("Start to fetch tzggs")
    tzggs = fetch_all_tzgg()

    tzggs = map(parse_data_from_tzgg_html, tzggs)
    tzggs = filter(lambda x: is_tzgg_date_after_target(x, fetch_date), tzggs)
    tzggs.reverse()
    logger.info("%s tzgg(s) to process" % len(tzggs))

    for tzgg in tzggs:
        tg = find_tzgg(tzgg["title"], tzgg["publish_date"])
        if not tg:
            logger.info(u"Found new tzgg: %s" % tzgg["title"])
            send_mail(tzgg)
            logger.info("Email sent successfully")
            create_tzgg(tzgg["title"], tzgg["url"], tzgg["publish_date"])

    CONN.close()


if __name__ == "__main__":
    main()
