import rethinkdb as r
actors = {
    "Felicity Turner": "6b8b8d4f-fe8b-4b0e-b257-973b17e343c5",
    "Desiree Harlech": "b1f52988-0971-42ab-a515-7c9b0d9f8d9c",
    "Amelia Bloom": "1002c758-8005-4b99-ba96-38c0faacffeb",
    "Don DeClaire": "67d37fb5-261b-41da-8d3f-2e5aff93ead1",
    "Bo Rakenfold": "1423bf50-6bfb-4eb6-997e-25dd1e801a98",
    "Lily Jordan": "244f62b1-ee51-444d-84c2-b72a39a2fdbd",
}


def create_rfid(name, user_id):
    return {
        "id": user_id,
        "publickey": None,
        "privatekey": None,
        "showid": None,
        "showdate": None,
        "name": name,
        "rfid": None,
    }


def create_perm(name, user_id):
    return {
        'name': name,
        'id': user_id,
        'delete_processor': False,
        'amelia_processor': True,
        'debug_processor': True,
        'interview_processor': True,
        'mental_health': True,
        'mirror_processor': True,
        'news_processor': True,
        'ownup': True,
        'pr0n_processor': True,
        'recommend_processor': True,
        'romance_processor': True,
        'tos_processor': True,
        'tracked_processor': True,
        'truth_processor': True
    }


if __name__ == "__main__":
    conn = r.connect(db='gulperbase')
    for name, user_id in actors.items():
        print("Adding: ", name)
        result = r.table("rfid").insert(create_rfid(name, user_id), conflict='update').run(conn)
        print(result)
        result = r.table("exhibitpermissions").insert(create_perm(name, user_id), conflict='update').run(conn)
        print(result)
