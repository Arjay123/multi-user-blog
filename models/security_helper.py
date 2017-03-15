import random


def make_salt(length = 5):
    """ Creates salt from random letters

    Args:
        length - length of salt string

    Returns:
        salt string
    """
    return ''.join(random.choice(letters) for x in xrange(length))


def make_pw_hash(name, pw, salt = None):
    """ creates hashed pw and salt string 
    
    Args:
        name - username
        pw - password
        salt - previous salt, used for checking valid pw instead of creating
    """
    if not salt:
        salt = make_salt()
    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (salt, h)