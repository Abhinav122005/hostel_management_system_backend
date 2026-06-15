import hashlib

def generate_payu_hash(key, txnid, amount, productinfo, firstname, email, salt):
    """
    Generates the PayU hash required to initiate a payment.
    Format: key|txnid|amount|productinfo|firstname|email|||||||||||salt
    """
    hash_string = f"{key}|{txnid}|{amount}|{productinfo}|{firstname}|{email}|||||||||||{salt}"
    return hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()

def verify_payu_hash(key, txnid, amount, productinfo, firstname, email, status, salt, posted_hash):
    """
    Verifies the hash received from PayU in the callback.
    Format: salt|status|||||||||||email|firstname|productinfo|amount|txnid|key
    """
    hash_string = f"{salt}|{status}|||||||||||{email}|{firstname}|{productinfo}|{amount}|{txnid}|{key}"
    calculated_hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()
    return calculated_hash == posted_hash.lower()
