from email_validator import validate_email, EmailNotValidError
import re


columns = ["profileName", "firstName", "lastName", "email", "phone", "line1", "line2", "line3", "city", "postCode"]

def check_errors(profile: dict) -> list:
    postcode_regex = re.compile(r"^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$")
    errors = []
    if not profile["profileName"].isalnum():
        errors.append("Invalid Profile Name (only alphanum)")
    if not profile["firstName"].isalpha() or not profile["lastName"].isalpha():
        errors.append("Invalid Names (only alphabet)")
    if len(profile["phone"]) not in [10,11] or profile["phone"][0] != "0" or not profile["phone"].isdigit():
        errors.append("Invalid Phone (start with 0)")
    if not re.match('[a-zA-Z\s]+$', profile["city"]):
        errors.append("Invalid City")
    if not postcode_regex.search(profile["postCode"].upper()):
        errors.append("Invalid Postcode")
    for i in columns:
        if i not in ["line2", "line3"] and not len(profile[i]):
            errors.append("Empty Values - Fill All Required Fields")
    try:
        valid = validate_email(profile["email"])
    except EmailNotValidError:
        errors.append("Invalid Email")
    
    return errors
