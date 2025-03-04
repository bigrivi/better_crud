USER_DATA = [
    {
        "id": 1,
        "email": "bob@gmail.com",
        "user_name": "bob",
        "password": "111111",
        "is_active": True,
        "is_superuser": True,
        "company_id": 1,
        "role_ids": [1, 2],
        "project_ids": [1, 2],
        "profile": {
            "name": "bob",
            "gender": "male",
            "phone": "111111",
            "birthdate": "2020-01-01",
            "hobby": "music",
            "state": "nice",
            "country": "china",
            "address": "anhui"
        },
        "staff": {
            "name": "bob",
            "position": "CEO",
            "job_title": "The Chief Executive Officer"
        },
        "tasks": [
            {
                "status": "pending",
                "description": "pending task"
            },
            {
                "status": "inprogress",
                "description": "inprogress task"
            },
            {
                "status": "completed",
                "description": "completed task"
            }
        ]
    },
    {
        "id": 2,
        "email": "alice@gmail.com",
        "user_name": "alice",
        "password": "111111",
        "is_active": True,
        "is_superuser": False,
        "company_id": 2,
        "role_ids": [2, 3],
        "project_ids": [2, 3],
        "profile": {
            "name": "alice",
            "gender": "female",
            "phone": "111111",
            "birthdate": "2010-01-01",
            "hobby": "music",
            "state": "nice",
            "country": "china",
            "address": "anhui"
        },
        "staff": {
            "name": "alice",
            "position": "CFO",
            "job_title": "Chief Financial Officer"
        },
        "tasks": [
            {
                "status": "pending",
                "description": "pending task"
            },
            {
                "status": "inprogress",
                "description": "inprogress task"
            },
            {
                "status": "completed",
                "description": "completed task"
            }
        ]
    },
    {
        "id": 3,
        "email": "jim@gmail.com",
        "user_name": "jim",
        "password": "111111",
        "is_active": True,
        "is_superuser": False,
        "company_id": 3,
        "role_ids": [2, 3],
        "project_ids": [2, 3],
        "profile": {
            "name": "jim",
            "gender": "male",
            "phone": "111111",
            "birthdate": "2022-01-01",
            "hobby": "music",
            "state": "nice",
            "country": "china",
            "address": "anhui"
        },
        "staff": {
            "name": "jim",
            "position": "QA",
            "job_title": "QA"
        },
        "tasks": [
            {
                "status": "pending",
                "description": "pending task"
            }
        ]
    },
    {
        "id": 4,
        "email": "tom@gmail.com",
        "user_name": "tom",
        "password": "111111",
        "is_active": False,
        "is_superuser": True,
        "company_id": 1,
        "role_ids": [1, 3],
        "project_ids": [1, 3],
        "profile": {
            "name": "tom",
            "gender": "male",
            "phone": "111111",
            "birthdate": "2024-01-01",
            "hobby": "music",
            "state": "nice",
            "country": "china",
            "address": None
        },
        "staff": {
            "name": "tom",
            "position": "RD",
            "job_title": "RD"
        },
        "tasks": [
            {
                "status": "pending",
                "description": "pending task"
            }
        ]
    }
]
