# Does Not use a Salt
import hashlib
def hash_password(password):
       # Create a new md5 hash object
       hasher = hashlib.md5()
       # Hash the password
       hasher.update(password.encode('utf-8'))
       # Get the hexadecimal representation of the hash
       hashed_password = hasher.hexdigest()
       return hashed_password




# uses a salt
import hashlib
def hash_password_salt(password):
        # Concatenate the salt and password
        salt = "QW66HJk(994634vv)"
        salted_password = salt + password
        # Create an MD5 hash object
        md5_hasher = hashlib.md5()
        # Update the hash object with the salted password
        md5_hasher.update(salted_password.encode('utf-8'))
        # Get the hexadecimal digest of the hash
        hashed_password = md5_hasher.hexdigest()
        return hashed_password




def verify_password_salt(hashed_password, input_password):
        # Get the salt used during hashing
        salt = "QW66HJk(994634vv)"
        # Concatenate the salt and input password
        salted_input_password = salt + input_password
        # Hash the salted input password
        hashed_input_password = hashlib.md5(salted_input_password.encode('utf-8')).hexdigest()
        # Compare the stored hashed password with the hashed input password
        return hashed_password == hashed_input_password

import re

def check_password_strength(password):
    if len(password) < 8:
        return "Must be eight characters"
    elif not re.search("[a-z]", password):
        return "Must have at least one small letter"
    elif not re.search("[A-Z]", password):
        return "Must have at least one capital letter"
    elif not re.search("[0-9]", password):
        return "Must have at least one number"
    elif not re.search("[_@#$]", password):
        return "Must have at least one symbol"
    else:
        common_patterns = [
            r'(?i)password',
            r'(?i)123456',
            r'(?i)qwerty',
            r'(?i)admin',
            r'(?i)root',
        ]
        for pattern in common_patterns:
            if re.search(pattern, password):
                return "Password too Simple"
        return "Password Correct - Strong Password"
