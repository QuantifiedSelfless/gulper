import cryptohelper


class User(object):
    def __init__(self, userid, publickey_pem, name, services=None,
                 privatekey_pem=None):
        self.userid = userid
        self.services = services
        self.publickey_pem = publickey_pem
        self.name = name
        if publickey_pem is not None:
            self.publickey = cryptohelper.import_key(publickey_pem)
        else:
            self.publickey = None
        if privatekey_pem is not None:
            self.privatekey = cryptohelper.import_key(privatekey_pem)
        else:
            self.privatekey = None
        self.data = {}

    def _save_process_results(self, results):
        #  TODO: should this ping back to QS or save in it's own DB?
        pass

    def encrypt_blob(self, data):
        return cryptohelper.encrypt_blob(self.publickey, data)

    def decrypt_blob(self, data):
        return cryptohelper.decrypt_blob(self.privatekey, data)
