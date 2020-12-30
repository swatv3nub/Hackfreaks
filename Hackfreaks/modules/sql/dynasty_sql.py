import threading

from Hackfreaks import dispatcher
from Hackfreaks.modules.sql import BASE, SESSION
from sqlalchemy import Boolean, Column, Integer, String, UnicodeText
from telegram.error import BadRequest, Unauthorized


class Dynasties(BASE):
    __tablename__ = "Dynasty"
    owner_id = Column(String(14))
    dynasty_name = Column(UnicodeText)
    dynasty_id = Column(UnicodeText, primary_key=True)
    dynasty_rules = Column(UnicodeText)
    dynasty_log = Column(UnicodeText)
    dynasty_users = Column(UnicodeText)

    def __init__(self, owner_id, dynasty_name, dynasty_id, dynasty_rules, dynasty_log,
                 dynasty_users):
        self.owner_id = owner_id
        self.dynasty_name = dynasty_name
        self.dynasty_id = dynasty_id
        self.dynasty_rules = dynasty_rules
        self.dynasty_log = dynasty_log
        self.dynasty_users = dynasty_users


class ChatD(BASE):
    __tablename__ = "chat_dynasties"
    chat_id = Column(String(14), primary_key=True)
    chat_name = Column(UnicodeText)
    dynasty_id = Column(UnicodeText)

    def __init__(self, chat_id, chat_name, dynasty_id):
        self.chat_id = chat_id
        self.chat_name = chat_name
        self.dynasty_id = dynasty_id


class BansD(BASE):
    __tablename__ = "bans_dynasties"
    dynasty_id = Column(UnicodeText, primary_key=True)
    user_id = Column(String(14), primary_key=True)
    first_name = Column(UnicodeText, nullable=False)
    last_name = Column(UnicodeText)
    user_name = Column(UnicodeText)
    reason = Column(UnicodeText, default="")
    time = Column(Integer, default=0)

    def __init__(self, dynasty_id, user_id, first_name, last_name, user_name,
                 reason, time):
        self.dynasty_id = dynasty_id
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.user_name = user_name
        self.reason = reason
        self.time = time


class DynastyUserSettings(BASE):
    __tablename__ = "dynasties_settings"
    user_id = Column(Integer, primary_key=True)
    should_report = Column(Boolean, default=True)

    def __init__(self, user_id):
        self.user_id = user_id

    def __repr__(self):
        return "<Dynasty report settings ({})>".format(self.user_id)


class DynastySubs(BASE):
    __tablename__ = "dynasties_subs"
    dynasty_id = Column(UnicodeText, primary_key=True)
    dynasty_subs = Column(UnicodeText, primary_key=True, nullable=False)

    def __init__(self, dynasty_id, dynasty_subs):
        self.dynasty_id = dynasty_id
        self.dynasty_subs = dynasty_subs

    def __repr__(self):
        return "<Dynasty {} subscribes for {}>".format(self.dynasty_id, self.dynasty_subs)


# Dropping db
# Dynastyerations.__table__.drop()
# ChatF.__table__.drop()
# BansF.__table__.drop()
# DynastySubs.__table__.drop()

Dynasties.__table__.create(checkfirst=True)
ChatD.__table__.create(checkfirst=True)
BansD.__table__.create(checkfirst=True)
DynastyUserSettings.__table__.create(checkfirst=True)
DynastySubs.__table__.create(checkfirst=True)

DYNASTY_LOCK = threading.RLock()
CHAT_DYNASTY_LOCK = threading.RLock()
DYNASTY_SETTINGS_LOCK = threading.RLock()
DYNASTY_SUBSCRIBER_LOCK = threading.RLock()

DYNASTY_BYNAME = {}
DYNASTY_BYOWNER = {}
DYNASTY_BYDYNASTYID = {}

DYNASTY_CHATS = {}
DYNASTY_CHATS_BYID = {}

DYNASTY_BANNED_FULL = {}
DYNASTY_BANNED_USERID = {}

DYNASTY_NOTIFICATION = {}
DYNASTY_SUBSCRIBER = {}
MYDYNASTY_SUBSCRIBER = {}


def get_dynasty_info(dynasty_id):
    get = DYNASTY_BYDYNASTYID.get(str(dynasty_id))
    if get is None:
        return False
    return get


def get_dynasty_id(chat_id):
    get = DYNASTY_CHATS.get(str(chat_id))
    if get is None:
        return False
    else:
        return get['fid']


def get_dynasty_name(chat_id):
    get = DYNASTY_CHATS.get(str(chat_id))
    if get is None:
        return False
    else:
        return get['chat_name']


def get_user_fban(dynasty_id, user_id):
    if not DYNASTY_BANNED_FULL.get(dynasty_id):
        return False, False, False
    user_info = DYNASTY_BANNED_FULL[dynasty_id].get(user_id)
    if not user_info:
        return None, None, None
    return user_info['first_name'], user_info['reason'], user_info['time']


def get_user_admin_dynasty_name(user_id):
    user_dynasties = []
    for f in DYNASTY_BYDYNASTYID:
        if int(user_id) in eval(
                eval(DYNASTY_BYDYNASTYID[f]['dusers'])['members']):
            user_dynasties.append(DYNASTY_BYDYNASTYID[f]['dname'])
    return user_dynasties


def get_user_owner_dynasty_name(user_id):
    user_dynasties = []
    for f in DYNASTY_BYDYNASTYID:
        if int(user_id) == int(eval(DYNASTY_BYDYNASTYID[f]['dusers'])['owner']):
            user_dynasties.append(DYNASTY_BYDYNASTYID[f]['dname'])
    return user_dynasties


def get_user_admin_dynasty_full(user_id):
    user_dynasties = []
    for f in DYNASTY_BYDYNASTYID:
        if int(user_id) in eval(
                eval(DYNASTY_BYDYNASTYID[f]['dusers'])['members']):
            user_dynasties.append({"dynasty_id": f, "dynasty": DYNASTY_BYDYNASTYID[f]})
    return user_dynasties


def get_user_owner_dynasty_full(user_id):
    user_dynasties = []
    for f in DYNASTY_BYDYNASTYID:
        if int(user_id) == int(eval(DYNASTY_BYDYNASTYID[f]['dusers'])['owner']):
            user_dynasties.append({"dynasty_id": f, "dynasty": DYNASTY_BYDYNASTYID[f]})
    return user_dynasties


def get_user_fbanlist(user_id):
    banlist = DYNASTY_BANNED_FULL
    user_name = ""
    dynastyname = []
    for x in banlist:
        if banlist[x].get(user_id):
            if user_name == "":
                user_name = banlist[x][user_id].get('first_name')
            dynastyname.append([x, banlist[x][user_id].get('reason')])
    return user_name, dynastyname


def new_dynasty(owner_id, dynasty_name, dynasty_id):
    with DYNASTY_LOCK:
        global DYNASTY_BYOWNER, DYNASTY_BYDYNASTYID, DYNASTY_BYNAME
        dynasty = Dynastyerations(
            str(owner_id), dynasty_name, str(dynasty_id),
            'Rules is not set in this Dynasty.', None,
            str({
                'owner': str(owner_id),
                'members': '[]'
            }))
        SESSION.add(dynasty)
        SESSION.commit()
        DYNASTY_BYOWNER[str(owner_id)] = ({
            'fid': str(dynasty_id),
            'dname': dynasty_name,
            'drules': 'Rules is not set in this Dynasty.',
            'dlog': None,
            'dusers': str({
                'owner': str(owner_id),
                'members': '[]'
            })
        })
        DYNASTY_BYDYNASTYID[str(dynasty_id)] = ({
            'owner': str(owner_id),
            'dname': dynasty_name,
            'drules': 'Rules is not set in this Dynasty.',
            'dlog': None,
            'dusers': str({
                'owner': str(owner_id),
                'members': '[]'
            })
        })
        DYNASTY_BYNAME[dynasty_name] = ({
            'fid': str(dynasty_id),
            'owner': str(owner_id),
            'drules': 'Rules is not set in this Dynasty.',
            'dlog': None,
            'dusers': str({
                'owner': str(owner_id),
                'members': '[]'
            })
        })
        return dynasty


def del_dynasty(dynasty_id):
    with DYNASTY_LOCK:
        global DYNASTY_BYOWNER, DYNASTY_BYDYNASTYID, DYNASTY_BYNAME, DYNASTY_CHATS, DYNASTY_CHATS_BYID, DYNASTY_BANNED_USERID, DYNASTY_BANNED_FULL
        getcache = DYNASTY_BYDYNASTYID.get(dynasty_id)
        if getcache is None:
            return False
        # Variables
        getdynasty = DYNASTY_BYDYNASTYID.get(dynasty_id)
        owner_id = getdynasty['owner']
        dynasty_name = getdynasty['dname']
        # Delete from cache
        DYNASTY_BYOWNER.pop(owner_id)
        DYNASTY_BYDYNASTYID.pop(dynasty_id)
        DYNASTY_BYNAME.pop(dynasty_name)
        if DYNASTY_CHATS_BYID.get(dynasty_id):
            for x in DYNASTY_CHATS_BYID[dynasty_id]:
                delchats = SESSION.query(ChatF).get(str(x))
                if delchats:
                    SESSION.delete(delchats)
                    SESSION.commit()
                DYNASTY_CHATS.pop(x)
            DYNASTY_CHATS_BYID.pop(dynasty_id)
        # Delete dynastyban users
        getall = DYNASTY_BANNED_USERID.get(dynasty_id)
        if getall:
            for x in getall:
                banlist = SESSION.query(BansF).get((dynasty_id, str(x)))
                if banlist:
                    SESSION.delete(banlist)
                    SESSION.commit()
        if DYNASTY_BANNED_USERID.get(dynasty_id):
            DYNASTY_BANNED_USERID.pop(dynasty_id)
        if DYNASTY_BANNED_FULL.get(dynasty_id):
            DYNASTY_BANNED_FULL.pop(dynasty_id)
        # Delete dynastiesubs
        getall = MYDYNASTY_SUBSCRIBER.get(dynasty_id)
        if getall:
            for x in getall:
                getsubs = SESSION.query(DynastySubs).get((dynasty_id, str(x)))
                if getsubs:
                    SESSION.delete(getsubs)
                    SESSION.commit()
        if DYNASTY_SUBSCRIBER.get(dynasty_id):
            DYNASTY_SUBSCRIBER.pop(dynasty_id)
        if MYDYNASTY_SUBSCRIBER.get(dynasty_id):
            MYDYNASTY_SUBSCRIBER.pop(dynasty_id)
        # Delete from database
        curr = SESSION.query(Dynastyerations).get(dynasty_id)
        if curr:
            SESSION.delete(curr)
            SESSION.commit()
        return True


def rename_dynasty(dynasty_id, owner_id, newname):
    with DYNASTY_LOCK:
        global DYNASTY_BYDYNASTYID, DYNASTY_BYOWNER, DYNASTY_BYNAME
        dynasty = SESSION.query(Dynastyerations).get(dynasty_id)
        if not dynasty:
            return False
        dynasty.dynasty_name = newname
        SESSION.commit()

        # Update the dicts
        oldname = DYNASTY_BYDYNASTYID[str(dynasty_id)]["dname"]
        tempdata = DYNASTY_BYNAME[oldname]
        DYNASTY_BYNAME.pop(oldname)

        DYNASTY_BYOWNER[str(owner_id)]["dname"] = newname
        DYNASTY_BYDYNASTYID[str(dynasty_id)]["dname"] = newname
        DYNASTY_BYNAME[newname] = tempdata
        return True


def chat_join_dynasty(dynasty_id, chat_name, chat_id):
    with DYNASTY_LOCK:
        global DYNASTY_CHATS, DYNASTY_CHATS_BYID
        r = ChatF(chat_id, chat_name, dynasty_id)
        SESSION.add(r)
        DYNASTY_CHATS[str(chat_id)] = {'chat_name': chat_name, 'fid': dynasty_id}
        checkid = DYNASTY_CHATS_BYID.get(dynasty_id)
        if checkid is None:
            DYNASTY_CHATS_BYID[dynasty_id] = []
        DYNASTY_CHATS_BYID[dynasty_id].append(str(chat_id))
        SESSION.commit()
        return r


def search_dynasty_by_name(dynasty_name):
    alldynasty = DYNASTY_BYNAME.get(dynasty_name)
    if alldynasty is None:
        return False
    return alldynasty


def search_user_in_dynasty(dynasty_id, user_id):
    getdynasty = DYNASTY_BYDYNASTYID.get(dynasty_id)
    if getdynasty is None:
        return False
    getdynasty = eval(getdynasty['dusers'])['members']
    if user_id in eval(getdynasty):
        return True
    else:
        return False


def user_demote_dynasty(dynasty_id, user_id):
    with DYNASTY_LOCK:
        global DYNASTY_BYOWNER, DYNASTY_BYDYNASTYID, DYNASTY_BYNAME
        # Variables
        getdynasty = DYNASTY_BYDYNASTYID.get(str(dynasty_id))
        owner_id = getdynasty['owner']
        dynasty_name = getdynasty['dname']
        dynasty_rules = getdynasty['drules']
        dynasty_log = getdynasty['dlog']
        # Temp set
        try:
            members = eval(eval(getdynasty['dusers'])['members'])
        except ValueError:
            return False
        members.remove(user_id)
        # Set user
        DYNASTY_BYOWNER[str(owner_id)]['dusers'] = str({
            'owner': str(owner_id),
            'members': str(members)
        })
        DYNASTY_BYDYNASTYID[str(dynasty_id)]['dusers'] = str({
            'owner': str(owner_id),
            'members': str(members)
        })
        DYNASTY_BYNAME[dynasty_name]['dusers'] = str({
            'owner': str(owner_id),
            'members': str(members)
        })
        # Set on database
        dynasty = Dynastyerations(
            str(owner_id), dynasty_name, str(dynasty_id), dynasty_rules, dynasty_log,
            str({
                'owner': str(owner_id),
                'members': str(members)
            }))
        SESSION.merge(dynasty)
        SESSION.commit()
        return True

        curr = SESSION.query(UserF).all()
        result = False
        for r in curr:
            if int(r.user_id) == int(user_id):
                if r.dynasty_id == dynasty_id:
                    SESSION.delete(r)
                    SESSION.commit()
                    result = True

        SESSION.close()
        return result


def user_join_dynasty(dynasty_id, user_id):
    with DYNASTY_LOCK:
        global DYNASTY_BYOWNER, DYNASTY_BYDYNASTYID, DYNASTY_BYNAME
        # Variables
        getdynasty = DYNASTY_BYDYNASTYID.get(str(dynasty_id))
        owner_id = getdynasty['owner']
        dynasty_name = getdynasty['dname']
        dynasty_rules = getdynasty['drules']
        dynasty_log = getdynasty['dlog']
        # Temp set
        members = eval(eval(getdynasty['dusers'])['members'])
        members.append(user_id)
        # Set user
        DYNASTY_BYOWNER[str(owner_id)]['dusers'] = str({
            'owner': str(owner_id),
            'members': str(members)
        })
        DYNASTY_BYDYNASTYID[str(dynasty_id)]['dusers'] = str({
            'owner': str(owner_id),
            'members': str(members)
        })
        DYNASTY_BYNAME[dynasty_name]['dusers'] = str({
            'owner': str(owner_id),
            'members': str(members)
        })
        # Set on database
        dynasty = Dynastyerations(
            str(owner_id), dynasty_name, str(dynasty_id), dynasty_rules, dynasty_log,
            str({
                'owner': str(owner_id),
                'members': str(members)
            }))
        SESSION.merge(dynasty)
        SESSION.commit()
        __load_all_dynasties_chats()
        return True


def chat_leave_dynasty(chat_id):
    with DYNASTY_LOCK:
        global DYNASTY_CHATS, DYNASTY_CHATS_BYID
        # Set variables
        dynasty_info = DYNASTY_CHATS.get(str(chat_id))
        if dynasty_info is None:
            return False
        dynasty_id = dynasty_info['fid']
        # Delete from cache
        DYNASTY_CHATS.pop(str(chat_id))
        DYNASTY_CHATS_BYID[str(dynasty_id)].remove(str(chat_id))
        # Delete from db
        curr = SESSION.query(ChatF).all()
        for U in curr:
            if int(U.chat_id) == int(chat_id):
                SESSION.delete(U)
                SESSION.commit()
        return True


def all_dynasty_chats(dynasty_id):
    with DYNASTY_LOCK:
        getdynasty = DYNASTY_CHATS_BYID.get(dynasty_id)
        if getdynasty is None:
            return []
        else:
            return getdynasty


def all_dynasty_users(dynasty_id):
    with DYNASTY_LOCK:
        getdynasty = DYNASTY_BYDYNASTYID.get(str(dynasty_id))
        if getdynasty is None:
            return False
        dynasty_owner = eval(eval(getdynasty['dusers'])['owner'])
        dynasty_admins = eval(eval(getdynasty['dusers'])['members'])
        dynasty_admins.append(dynasty_owner)
        return dynasty_admins


def all_dynasty_members(dynasty_id):
    with DYNASTY_LOCK:
        getdynasty = DYNASTY_BYDYNASTYID.get(str(dynasty_id))
        dynasty_admins = eval(eval(getdynasty['dusers'])['members'])
        return dynasty_admins


def set_drules(dynasty_id, rules):
    with DYNASTY_LOCK:
        global DYNASTY_BYOWNER, DYNASTY_BYDYNASTYID, DYNASTY_BYNAME
        # Variables
        getdynasty = DYNASTY_BYDYNASTYID.get(str(dynasty_id))
        owner_id = getdynasty['owner']
        dynasty_name = getdynasty['dname']
        dynasty_members = getdynasty['dusers']
        dynasty_rules = str(rules)
        dynasty_log = getdynasty['dlog']
        # Set user
        DYNASTY_BYOWNER[str(owner_id)]['drules'] = dynasty_rules
        DYNASTY_BYDYNASTYID[str(dynasty_id)]['drules'] = dynasty_rules
        DYNASTY_BYNAME[dynasty_name]['drules'] = dynasty_rules
        # Set on database
        dynasty = Dynastyerations(
            str(owner_id), dynasty_name, str(dynasty_id), dynasty_rules, dynasty_log,
            str(dynasty_members))
        SESSION.merge(dynasty)
        SESSION.commit()
        return True


def get_drules(dynasty_id):
    with DYNASTY_LOCK:
        rules = DYNASTY_BYDYNASTYID[str(dynasty_id)]['drules']
        return rules


def fban_user(dynasty_id, user_id, first_name, last_name, user_name, reason, time):
    with DYNASTY_LOCK:
        r = SESSION.query(BansF).all()
        for I in r:
            if I.dynasty_id == dynasty_id:
                if int(I.user_id) == int(user_id):
                    SESSION.delete(I)

        r = BansF(
            str(dynasty_id), str(user_id), first_name, last_name, user_name, reason,
            time)

        SESSION.add(r)
        try:
            SESSION.commit()
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.commit()
        __load_all_dynasties_banned()
        return r


def multi_fban_user(multi_dynasty_id, multi_user_id, multi_first_name,
                    multi_last_name, multi_user_name, multi_reason):
    if True:  # with DYNASTY_LOCK:
        counter = 0
        time = 0
        for x in range(len(multi_dynasty_id)):
            dynasty_id = multi_dynasty_id[x]
            user_id = multi_user_id[x]
            first_name = multi_first_name[x]
            last_name = multi_last_name[x]
            user_name = multi_user_name[x]
            reason = multi_reason[x]
            r = SESSION.query(BansF).all()
            for I in r:
                if I.dynasty_id == dynasty_id:
                    if int(I.user_id) == int(user_id):
                        SESSION.delete(I)

            r = BansF(
                str(dynasty_id), str(user_id), first_name, last_name, user_name,
                reason, time)

            SESSION.add(r)
            counter += 1
            if str(str(counter)[-2:]) == "00":
                print(user_id)
                print(first_name)
                print(reason)
                print(counter)
        try:
            SESSION.commit()
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.commit()
        __load_all_dynasties_banned()
        print("Done")
        return counter


def un_fban_user(dynasty_id, user_id):
    with DYNASTY_LOCK:
        r = SESSION.query(BansF).all()
        for I in r:
            if I.dynasty_id == dynasty_id:
                if int(I.user_id) == int(user_id):
                    SESSION.delete(I)
        try:
            SESSION.commit()
        except:
            SESSION.rollback()
            return False
        finally:
            SESSION.commit()
        __load_all_dynasties_banned()
        return I


def get_fban_user(dynasty_id, user_id):
    list_fbanned = DYNASTY_BANNED_USERID.get(dynasty_id)
    if list_fbanned is None:
        DYNASTY_BANNED_USERID[dynasty_id] = []
    if user_id in DYNASTY_BANNED_USERID[dynasty_id]:
        r = SESSION.query(BansF).all()
        reason = None
        for I in r:
            if I.dynasty_id == dynasty_id:
                if int(I.user_id) == int(user_id):
                    reason = I.reason
                    time = I.time
        return True, reason, time
    else:
        return False, None, None


def get_all_fban_users(dynasty_id):
    list_fbanned = DYNASTY_BANNED_USERID.get(dynasty_id)
    if list_fbanned is None:
        DYNASTY_BANNED_USERID[dynasty_id] = []
    return DYNASTY_BANNED_USERID[dynasty_id]


def get_all_fban_users_target(dynasty_id, user_id):
    list_fbanned = DYNASTY_BANNED_FULL.get(dynasty_id)
    if list_fbanned is None:
        DYNASTY_BANNED_FULL[dynasty_id] = []
        return False
    getuser = list_fbanned[str(user_id)]
    return getuser


def get_all_fban_users_global():
    list_fbanned = DYNASTY_BANNED_USERID
    total = []
    for x in list(DYNASTY_BANNED_USERID):
        for y in DYNASTY_BANNED_USERID[x]:
            total.append(y)
    return total


def get_all_dynasties_users_global():
    list_dynasty = DYNASTY_BYDYNASTYID
    total = []
    for x in list(DYNASTY_BYDYNASTYID):
        total.append(DYNASTY_BYDYNASTYID[x])
    return total


def search_dynasty_by_id(dynasty_id):
    get = DYNASTY_BYDYNASTYID.get(dynasty_id)
    if get is None:
        return False
    else:
        return get
    result = False
    for Q in curr:
        if Q.dynasty_id == dynasty_id:
            result = Q.dynasty_id

    return result


def user_dynasties_report(user_id: int) -> bool:
    user_setting = DYNASTY_NOTIFICATION.get(str(user_id))
    if user_setting is None:
        user_setting = True
    return user_setting


def set_dynasties_setting(user_id: int, setting: bool):
    with DYNASTY_SETTINGS_LOCK:
        global DYNASTY_NOTIFICATION
        user_setting = SESSION.query(DynastyUserSettings).get(user_id)
        if not user_setting:
            user_setting = DynastyUserSettings(user_id)

        user_setting.should_report = setting
        DYNASTY_NOTIFICATION[str(user_id)] = setting
        SESSION.add(user_setting)
        SESSION.commit()


def get_dynasty_log(dynasty_id):
    dynasty_setting = DYNASTY_BYDYNASTYID.get(str(dynasty_id))
    if dynasty_setting is None:
        dynasty_setting = False
        return dynasty_setting
    if dynasty_setting.get('dlog') is None:
        return False
    elif dynasty_setting.get('dlog'):
        try:
            dispatcher.bot.get_chat(dynasty_setting.get('dlog'))
        except BadRequest:
            set_dynasty_log(dynasty_id, None)
            return False
        except Unauthorized:
            set_dynasty_log(dynasty_id, None)
            return False
        return dynasty_setting.get('dlog')
    else:
        return False


def set_dynasty_log(dynasty_id, chat_id):
    with DYNASTY_LOCK:
        global DYNASTY_BYOWNER, DYNASTY_BYDYNASTYID, DYNASTY_BYNAME
        # Variables
        getdynasty = DYNASTY_BYDYNASTYID.get(str(dynasty_id))
        owner_id = getdynasty['owner']
        dynasty_name = getdynasty['dname']
        dynasty_members = getdynasty['dusers']
        dynasty_rules = getdynasty['drules']
        dynasty_log = str(chat_id)
        # Set user
        DYNASTY_BYOWNER[str(owner_id)]['dlog'] = dynasty_log
        DYNASTY_BYDYNASTYID[str(dynasty_id)]['dlog'] = dynasty_log
        DYNASTY_BYNAME[dynasty_name]['dlog'] = dynasty_log
        # Set on database
        dynasty = Dynastyerations(
            str(owner_id), dynasty_name, str(dynasty_id), dynasty_rules, dynasty_log,
            str(dynasty_members))
        SESSION.merge(dynasty)
        SESSION.commit()
        print(dynasty_log)
        return True


def subs_dynasty(dynasty_id, my_dynasty):
    check = get_spec_subs(dynasty_id, my_dynasty)
    if check:
        return False
    with DYNASTY_SUBSCRIBER_LOCK:
        subsdynasty = DynastySubs(dynasty_id, my_dynasty)

        SESSION.merge(subsdynasty)  # merge to avoid duplicate key issues
        SESSION.commit()
        global DYNASTY_SUBSCRIBER
        if DYNASTY_SUBSCRIBER.get(dynasty_id, set()) == set():
            DYNASTY_SUBSCRIBER[dynasty_id] = {my_dynasty}
        else:
            DYNASTY_SUBSCRIBER.get(dynasty_id, set()).add(my_dynasty)
        return True


def unsubs_dynasty(dynasty_id, my_dynasty):
    with DYNASTY_SUBSCRIBER_LOCK:
        getsubs = SESSION.query(DynastySubs).get((dynasty_id, my_dynasty))
        if getsubs:
            if my_dynasty in DYNASTY_SUBSCRIBER.get(dynasty_id, set()):  # sanity check
                DYNASTY_SUBSCRIBER.get(dynasty_id, set()).remove(my_dynasty)

            SESSION.delete(getsubs)
            SESSION.commit()
            return True

        SESSION.close()
        return False


def get_all_subs(dynasty_id):
    return DYNASTY_SUBSCRIBER.get(dynasty_id, set())


def get_spec_subs(dynasty_id, dynasty_target):
    if DYNASTY_SUBSCRIBER.get(dynasty_id, set()) == set():
        return {}
    else:
        return DYNASTY_SUBSCRIBER.get(dynasty_id, dynasty_target)


def get_mysubs(my_dynasty):
    return list(MYDYNASTY_SUBSCRIBER.get(my_dynasty))


def get_subscriber(dynasty_id):
    return DYNASTY_SUBSCRIBER.get(dynasty_id, set())


def __load_all_dynasties():
    global DYNASTY_BYOWNER, DYNASTY_BYDYNASTYID, DYNASTY_BYNAME
    try:
        dynasties = SESSION.query(Dynastyerations).all()
        for x in dynasties:  # remove tuple by ( ,)
            # Dynasty by Owner
            check = DYNASTY_BYOWNER.get(x.owner_id)
            if check is None:
                DYNASTY_BYOWNER[x.owner_id] = []
            DYNASTY_BYOWNER[str(x.owner_id)] = {
                'fid': str(x.dynasty_id),
                'dname': x.dynasty_name,
                'drules': x.dynasty_rules,
                'dlog': x.dynasty_log,
                'dusers': str(x.dynasty_users)
            }
            # Dynasty By DynastyId
            check = DYNASTY_BYDYNASTYID.get(x.dynasty_id)
            if check is None:
                DYNASTY_BYDYNASTYID[x.dynasty_id] = []
            DYNASTY_BYDYNASTYID[str(x.dynasty_id)] = {
                'owner': str(x.owner_id),
                'dname': x.dynasty_name,
                'drules': x.dynasty_rules,
                'dlog': x.dynasty_log,
                'dusers': str(x.dynasty_users)
            }
            # Dynasty By Name
            check = DYNASTY_BYNAME.get(x.dynasty_name)
            if check is None:
                DYNASTY_BYNAME[x.dynasty_name] = []
            DYNASTY_BYNAME[x.dynasty_name] = {
                'fid': str(x.dynasty_id),
                'owner': str(x.owner_id),
                'drules': x.dynasty_rules,
                'dlog': x.dynasty_log,
                'dusers': str(x.dynasty_users)
            }
    finally:
        SESSION.close()


def __load_all_dynasties_chats():
    global DYNASTY_CHATS, DYNASTY_CHATS_BYID
    try:
        qall = SESSION.query(ChatF).all()
        DYNASTY_CHATS = {}
        DYNASTY_CHATS_BYID = {}
        for x in qall:
            # Dynastyeration Chats
            check = DYNASTY_CHATS.get(x.chat_id)
            if check is None:
                DYNASTY_CHATS[x.chat_id] = {}
            DYNASTY_CHATS[x.chat_id] = {
                'chat_name': x.chat_name,
                'fid': x.dynasty_id
            }
            # Dynastyeration Chats By ID
            check = DYNASTY_CHATS_BYID.get(x.dynasty_id)
            if check is None:
                DYNASTY_CHATS_BYID[x.dynasty_id] = []
            DYNASTY_CHATS_BYID[x.dynasty_id].append(x.chat_id)
    finally:
        SESSION.close()


def __load_all_dynasties_banned():
    global DYNASTY_BANNED_USERID, DYNASTY_BANNED_FULL
    try:
        DYNASTY_BANNED_USERID = {}
        DYNASTY_BANNED_FULL = {}
        qall = SESSION.query(BansF).all()
        for x in qall:
            check = DYNASTY_BANNED_USERID.get(x.dynasty_id)
            if check is None:
                DYNASTY_BANNED_USERID[x.dynasty_id] = []
            if int(x.user_id) not in DYNASTY_BANNED_USERID[x.dynasty_id]:
                DYNASTY_BANNED_USERID[x.dynasty_id].append(int(x.user_id))
            check = DYNASTY_BANNED_FULL.get(x.dynasty_id)
            if check is None:
                DYNASTY_BANNED_FULL[x.dynasty_id] = {}
            DYNASTY_BANNED_FULL[x.dynasty_id][x.user_id] = {
                'first_name': x.first_name,
                'last_name': x.last_name,
                'user_name': x.user_name,
                'reason': x.reason,
                'time': x.time
            }
    finally:
        SESSION.close()


def __load_all_dynasties_settings():
    global DYNASTY_NOTIFICATION
    try:
        getuser = SESSION.query(DynastyUserSettings).all()
        for x in getuser:
            DYNASTY_NOTIFICATION[str(x.user_id)] = x.should_report
    finally:
        SESSION.close()


def __load_dynasties_subscriber():
    global DYNASTY_SUBSCRIBER
    global MYDYNASTY_SUBSCRIBER
    try:
        dynasties = SESSION.query(DynastySubs.dynasty_id).distinct().all()
        for (dynasty_id,) in dynasties:  # remove tuple by ( ,)
            DYNASTY_SUBSCRIBER[dynasty_id] = []
            MYDYNASTY_SUBSCRIBER[dynasty_id] = []

        all_dynastiesubs = SESSION.query(DynastySubs).all()
        for x in all_dynastiesubs:
            DYNASTY_SUBSCRIBER[x.dynasty_id] += [x.dynasty_subs]
            try:
                MYDYNASTY_SUBSCRIBER[x.dynasty_subs] += [x.dynasty_id]
            except KeyError:
                getsubs = SESSION.query(DynastySubs).get((x.dynasty_id, x.dynasty_subs))
                if getsubs:
                    SESSION.delete(getsubs)
                    SESSION.commit()

        DYNASTY_SUBSCRIBER = {x: set(y) for x, y in DYNASTY_SUBSCRIBER.items()}
        MYDYNASTY_SUBSCRIBER = {x: set(y) for x, y in MYDYNASTY_SUBSCRIBER.items()}

    finally:
        SESSION.close()


__load_all_dynasties()
__load_all_dynasties_chats()
__load_all_dynasties_banned()
__load_all_dynasties_settings()
__load_dynasties_subscriber()
