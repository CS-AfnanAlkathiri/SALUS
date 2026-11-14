"""Run against a local built instance: python tests/browser_demo.py [base URL]."""
import re
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
screens = Path(sys.argv[2]) if len(sys.argv) > 2 else None

def settings(page, crew, day):
    page.get_by_role("button", name="Mission settings").click()
    page.get_by_label("Crew member").select_option(crew)
    page.get_by_role("spinbutton", name="Mission day").fill(str(day))
    page.get_by_role("button", name="Done").click()
    expect(page.locator(".day-chip")).to_contain_text(str(day))

def begin(page, region, concern):
    page.get_by_role("link", name="Explore", exact=True).click()
    page.get_by_role("button", name=region, exact=True).focus()
    page.keyboard.press("Enter")
    page.get_by_role("link", name=concern, exact=True).click()
    page.get_by_role("button", name="Begin assessment").click()

def choose(page, label):
    page.get_by_role("radio", name=label, exact=True).check()
    page.get_by_role("button", name="Continue").click()

def number(page, prompt, value):
    page.get_by_role("spinbutton", name=prompt).fill(str(value))
    page.get_by_role("button", name="Continue").click()

with sync_playwright() as playwright:
    chromium = playwright.chromium
    executable = "/usr/bin/chromium" if Path("/usr/bin/chromium").exists() else None
    browser = chromium.launch(executable_path=executable, args=["--no-sandbox"])
    page = browser.new_page(viewport={"width":1440,"height":900})
    page.set_default_timeout(10000)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(base)
    expect(page.get_by_role("heading", name="Health overview")).to_be_visible()
    expect(page.get_by_text("72.8", exact=False).first).to_be_visible()
    if screens:
        screens.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=screens/"desktop.png", full_page=True)
    begin(page,"General health","Fatigue")
    choose(page,"No")
    choose(page,"Today")
    choose(page,"No")
    page.get_by_text("How to measure",exact=True).click()
    expect(page.get_by_text("After resting,",exact=False)).to_be_visible()
    number(page,"Record your resting heart rate",72.8)
    page.get_by_role("link",name="Save & exit").click()
    page.get_by_role("link",name=re.compile(r"Fatigue.*In progress", re.I)).first.click()
    number(page,"Record your sleep duration",5.47)
    number(page,"Record your fatigue",7)
    page.get_by_role("button",name="View results").click()
    expect(page.get_by_text("Unusual pattern flagged")).to_be_visible()
    expect(page.get_by_role("heading",name="Risk of Inadequate Sleep and Irregular Schedules")).to_be_visible()
    if screens:
        page.screenshot(path=screens/"results.png",full_page=True)
    page.get_by_role("link",name="Explore",exact=True).click()
    settings(page,"AST-03",49)
    begin(page,"Cardiovascular","Palpitations")
    choose(page,"No")
    choose(page,"Today")
    choose(page,"No")
    number(page,"Record your resting heart rate",71.6)
    number(page,"Record your sleep duration",7.09)
    number(page,"Record your systolic blood pressure",123)
    number(page,"Record your diastolic blood pressure",75)
    page.get_by_role("button",name="View results").click()
    expect(page.get_by_role("heading",name="Risk of Cardiovascular Adaptations")).to_be_visible()
    page.get_by_role("link",name="Explore",exact=True).click()
    settings(page,"AST-01",60)
    begin(page,"Cardiovascular","Chest discomfort")
    choose(page,"Yes")
    expect(page.get_by_role("heading",name="Emergency Assistance")).to_be_visible()
    expect(page.get_by_text("The routine assessment was interrupted.")).to_be_visible()
    assert not errors, errors
    page.close()
    mobile = browser.new_page(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True)
    mobile.goto(base)
    expect(mobile.get_by_role("heading",name="Health overview")).to_be_visible()
    expect(mobile.get_by_role("link",name="Emergency",exact=True)).to_be_visible()
    mobile.get_by_role("button",name="Head & brain",exact=True).tap()
    expect(mobile.get_by_role("heading",name="Head & Brain")).to_be_visible()
    assert mobile.evaluate("document.documentElement.scrollWidth === innerWidth")
    if screens:
        mobile.screenshot(path=screens/"mobile.png",full_page=True)
    browser.close()
    print("Passed: desktop fatigue and resume, cardiovascular, emergency, keyboard anatomy, mobile touch and overflow.")
