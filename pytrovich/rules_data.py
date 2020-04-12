# coding: utf-8


def rules():
    # NOTA BENE: outdated, works only in case `petrovich-rules` are not accessible for some reason
    return {
        "lastname": {
            "exceptions": [
                {
                    "gender": "androgynous",
                    "test": [
                        "бонч",
                        "абдул",
                        "белиц",
                        "гасан",
                        "дюссар",
                        "дюмон",
                        "книппер",
                        "корвин",
                        "ван",
                        "шолом",
                        "тер",
                        "призван",
                        "мелик",
                        "вар",
                        "фон"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ],
                    "tags": [
                        "first_word"
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "дюма",
                        "тома",
                        "дега",
                        "люка",
                        "ферма",
                        "гамарра",
                        "петипа",
                        "шандра",
                        "скаля",
                        "каруана"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "гусь",
                        "ремень",
                        "камень",
                        "онук",
                        "богода",
                        "нечипас",
                        "долгопалец",
                        "маненок",
                        "рева",
                        "кива"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "вий",
                        "сой",
                        "цой",
                        "хой"
                    ],
                    "mods": [
                        "-я",
                        "-ю",
                        "-я",
                        "-ем",
                        "-е"
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "я"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                }
            ],
            "suffixes": [
                {
                    "gender": "female",
                    "test": [
                        "б",
                        "в",
                        "г",
                        "д",
                        "ж",
                        "з",
                        "й",
                        "к",
                        "л",
                        "м",
                        "н",
                        "п",
                        "р",
                        "с",
                        "т",
                        "ф",
                        "х",
                        "ц",
                        "ч",
                        "ш",
                        "щ",
                        "ъ",
                        "ь"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "гава",
                        "орота"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "ска",
                        "цка"
                    ],
                    "mods": [
                        "-ой",
                        "-ой",
                        "-ую",
                        "-ой",
                        "-ой"
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "цкая",
                        "ская",
                        "ная",
                        "ая"
                    ],
                    "mods": [
                        "--ой",
                        "--ой",
                        "--ую",
                        "--ой",
                        "--ой"
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "яя"
                    ],
                    "mods": [
                        "--ей",
                        "--ей",
                        "--юю",
                        "--ей",
                        "--ей"
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "на"
                    ],
                    "mods": [
                        "-ой",
                        "-ой",
                        "-у",
                        "-ой",
                        "-ой"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "иной"
                    ],
                    "mods": [
                        "-я",
                        "-ю",
                        "-я",
                        "-ем",
                        "-е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "уй"
                    ],
                    "mods": [
                        "-я",
                        "-ю",
                        "-я",
                        "-ем",
                        "-е"
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "ца"
                    ],
                    "mods": [
                        "-ы",
                        "-е",
                        "-у",
                        "-ей",
                        "-е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "рих"
                    ],
                    "mods": [
                        "а",
                        "у",
                        "а",
                        "ом",
                        "е"
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "ия"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "иа",
                        "аа",
                        "оа",
                        "уа",
                        "ыа",
                        "еа",
                        "юа",
                        "эа"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "их",
                        "ых"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "о",
                        "е",
                        "э",
                        "и",
                        "ы",
                        "у",
                        "ю"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "ова",
                        "ева"
                    ],
                    "mods": [
                        "-ой",
                        "-ой",
                        "-у",
                        "-ой",
                        "-ой"
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "га",
                        "ка",
                        "ха",
                        "ча",
                        "ща",
                        "жа",
                        "ша"
                    ],
                    "mods": [
                        "-и",
                        "-е",
                        "-у",
                        "-ой",
                        "-е"
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "а"
                    ],
                    "mods": [
                        "-ы",
                        "-е",
                        "-у",
                        "-ой",
                        "-е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ь"
                    ],
                    "mods": [
                        "-я",
                        "-ю",
                        "-я",
                        "-ем",
                        "-е"
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "ия"
                    ],
                    "mods": [
                        "-и",
                        "-и",
                        "-ю",
                        "-ей",
                        "-и"
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "я"
                    ],
                    "mods": [
                        "-и",
                        "-е",
                        "-ю",
                        "-ей",
                        "-е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ей"
                    ],
                    "mods": [
                        "-я",
                        "-ю",
                        "-я",
                        "-ем",
                        "-е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ян",
                        "ан",
                        "йн"
                    ],
                    "mods": [
                        "а",
                        "у",
                        "а",
                        "ом",
                        "е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ынец",
                        "обец"
                    ],
                    "mods": [
                        "--ца",
                        "--цу",
                        "--ца",
                        "--цем",
                        "--це"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "онец",
                        "овец"
                    ],
                    "mods": [
                        "--ца",
                        "--цу",
                        "--ца",
                        "--цом",
                        "--це"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ай"
                    ],
                    "mods": [
                        "-я",
                        "-ю",
                        "-я",
                        "-ем",
                        "-е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "кой"
                    ],
                    "mods": [
                        "-го",
                        "-му",
                        "-го",
                        "--им",
                        "-м"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "гой"
                    ],
                    "mods": [
                        "-го",
                        "-му",
                        "-го",
                        "--им",
                        "-м"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ой"
                    ],
                    "mods": [
                        "-го",
                        "-му",
                        "-го",
                        "--ым",
                        "-м"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ах",
                        "ив"
                    ],
                    "mods": [
                        "а",
                        "у",
                        "а",
                        "ом",
                        "е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ший",
                        "щий",
                        "жий",
                        "ний"
                    ],
                    "mods": [
                        "--его",
                        "--ему",
                        "--его",
                        "-м",
                        "--ем"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ый"
                    ],
                    "mods": [
                        "--ого",
                        "--ому",
                        "--ого",
                        "-м",
                        "--ом"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "кий"
                    ],
                    "mods": [
                        "--ого",
                        "--ому",
                        "--ого",
                        "-м",
                        "--ом"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ий"
                    ],
                    "mods": [
                        "-я",
                        "-ю",
                        "-я",
                        "-ем",
                        "-и"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ок"
                    ],
                    "mods": [
                        "--ка",
                        "--ку",
                        "--ка",
                        "--ком",
                        "--ке"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ец"
                    ],
                    "mods": [
                        "--ца",
                        "--цу",
                        "--ца",
                        "--цом",
                        "--це"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ц",
                        "ч",
                        "ш",
                        "щ"
                    ],
                    "mods": [
                        "а",
                        "у",
                        "а",
                        "ем",
                        "е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ен",
                        "нн",
                        "он",
                        "ун"
                    ],
                    "mods": [
                        "а",
                        "у",
                        "а",
                        "ом",
                        "е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "в",
                        "н"
                    ],
                    "mods": [
                        "а",
                        "у",
                        "а",
                        "ым",
                        "е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "б",
                        "г",
                        "д",
                        "ж",
                        "з",
                        "к",
                        "л",
                        "м",
                        "п",
                        "р",
                        "с",
                        "т",
                        "ф",
                        "х"
                    ],
                    "mods": [
                        "а",
                        "у",
                        "а",
                        "ом",
                        "е"
                    ]
                }
            ]
        },
        "firstname": {
            "exceptions": [
                {
                    "gender": "male",
                    "test": [
                        "лев"
                    ],
                    "mods": [
                        "--ьва",
                        "--ьву",
                        "--ьва",
                        "--ьвом",
                        "--ьве"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "пётр"
                    ],
                    "mods": [
                        "---етра",
                        "---етру",
                        "---етра",
                        "---етром",
                        "---етре"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "павел"
                    ],
                    "mods": [
                        "--ла",
                        "--лу",
                        "--ла",
                        "--лом",
                        "--ле"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "яша"
                    ],
                    "mods": [
                        "-и",
                        "-е",
                        "-у",
                        "-ей",
                        "-е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "шота"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "рашель",
                        "нинель",
                        "николь",
                        "габриэль",
                        "даниэль"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                }
            ],
            "suffixes": [
                {
                    "gender": "androgynous",
                    "test": [
                        "е",
                        "ё",
                        "и",
                        "о",
                        "у",
                        "ы",
                        "э",
                        "ю"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "б",
                        "в",
                        "г",
                        "д",
                        "ж",
                        "з",
                        "й",
                        "к",
                        "л",
                        "м",
                        "н",
                        "п",
                        "р",
                        "с",
                        "т",
                        "ф",
                        "х",
                        "ц",
                        "ч",
                        "ш",
                        "щ",
                        "ъ"
                    ],
                    "mods": [
                        ".",
                        ".",
                        ".",
                        ".",
                        "."
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "ь"
                    ],
                    "mods": [
                        "-и",
                        "-и",
                        ".",
                        "ю",
                        "-и"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ь"
                    ],
                    "mods": [
                        "-я",
                        "-ю",
                        "-я",
                        "-ем",
                        "-е"
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "га",
                        "ка",
                        "ха",
                        "ча",
                        "ща",
                        "жа"
                    ],
                    "mods": [
                        "-и",
                        "-е",
                        "-у",
                        "-ой",
                        "-е"
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "ша"
                    ],
                    "mods": [
                        "-и",
                        "-е",
                        "-у",
                        "-ей",
                        "-е"
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "а"
                    ],
                    "mods": [
                        "-ы",
                        "-е",
                        "-у",
                        "-ой",
                        "-е"
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "ия"
                    ],
                    "mods": [
                        "-и",
                        "-и",
                        "-ю",
                        "-ей",
                        "-и"
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "а"
                    ],
                    "mods": [
                        "-ы",
                        "-е",
                        "-у",
                        "-ой",
                        "-е"
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "я"
                    ],
                    "mods": [
                        "-и",
                        "-е",
                        "-ю",
                        "-ей",
                        "-е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ия"
                    ],
                    "mods": [
                        "-и",
                        "-и",
                        "-ю",
                        "-ей",
                        "-и"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "я"
                    ],
                    "mods": [
                        "-и",
                        "-е",
                        "-ю",
                        "-ей",
                        "-е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ей"
                    ],
                    "mods": [
                        "-я",
                        "-ю",
                        "-я",
                        "-ем",
                        "-е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "ий"
                    ],
                    "mods": [
                        "-я",
                        "-ю",
                        "-я",
                        "-ем",
                        "-и"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "й"
                    ],
                    "mods": [
                        "-я",
                        "-ю",
                        "-я",
                        "-ем",
                        "-е"
                    ]
                },
                {
                    "gender": "male",
                    "test": [
                        "б",
                        "в",
                        "г",
                        "д",
                        "ж",
                        "з",
                        "к",
                        "л",
                        "м",
                        "н",
                        "п",
                        "р",
                        "с",
                        "т",
                        "ф",
                        "х",
                        "ц",
                        "ч"
                    ],
                    "mods": [
                        "а",
                        "у",
                        "а",
                        "ом",
                        "е"
                    ]
                },
                {
                    "gender": "androgynous",
                    "test": [
                        "ния",
                        "рия",
                        "вия"
                    ],
                    "mods": [
                        "-и",
                        "-и",
                        "-ю",
                        "-ем",
                        "-ем"
                    ]
                }
            ]
        },
        "middlename": {
            "suffixes": [
                {
                    "gender": "male",
                    "test": [
                        "ич"
                    ],
                    "mods": [
                        "а",
                        "у",
                        "а",
                        "ем",
                        "е"
                    ]
                },
                {
                    "gender": "female",
                    "test": [
                        "на"
                    ],
                    "mods": [
                        "-ы",
                        "-е",
                        "-у",
                        "-ой",
                        "-е"
                    ]
                }
            ]
        }
    }