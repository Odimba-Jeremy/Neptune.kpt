import json
import os
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, session

app = Flask(__name__)
from flask_cors import CORS
CORS(app,
     supports_credentials=True,
     origins=[
        "http://localhost:3000",
        "https://neptune-kpt.onrender.com"
     ])
app.config['SECRET_KEY'] = 'campus-connect-secret-key-2026'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

# ============================================================
# GESTION DES FICHIERS JSON
# ============================================================
DATA_DIR = 'data'

os.makedirs(DATA_DIR, exist_ok=True)

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
POSTS_FILE = os.path.join(DATA_DIR, 'posts.json')
CONVERSATIONS_FILE = os.path.join(DATA_DIR, 'conversations.json')
MESSAGES_FILE = os.path.join(DATA_DIR, 'messages.json')
NOTIFICATIONS_FILE = os.path.join(DATA_DIR, 'notifications.json')
RECOVERIES_FILE = os.path.join(DATA_DIR, 'recoveries.json')
BROADCASTS_FILE = os.path.join(DATA_DIR, 'broadcasts.json')
ADS_FILE = os.path.join(DATA_DIR, 'ads.json')
AUDIT_FILE = os.path.join(DATA_DIR, 'audit.json')
GROUPS_FILE = os.path.join(DATA_DIR, 'groups.json')
EVENTS_FILE = os.path.join(DATA_DIR, 'events.json')
MARKETPLACE_FILE = os.path.join(DATA_DIR, 'marketplace.json')

def load_json(filepath, default=[]):
    if not os.path.exists(filepath):
        return default
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)

def init_data():
    if not os.path.exists(USERS_FILE):
        hashed = 'fake_hash_admin'
        admin = {
            'id': 1,
            'uuid': str(uuid.uuid4()),
            'email': 'admin@campusconnect.app',
            'password': 'Admin@2026',
            'full_name': 'Administrateur Principal',
            'university': 'Campus Central',
            'role': 'admin',
            'status': 'active',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        save_json(USERS_FILE, [admin])
    
    if not os.path.exists(GROUPS_FILE):
        save_json(GROUPS_FILE, [
            {'id': 1, 'title': 'Club Informatique', 'description': 'Échange sur les technologies', 'tag': 'Tech', 'members': 45},
            {'id': 2, 'title': 'Bibliothèque', 'description': 'Partage de ressources', 'tag': 'Académique', 'members': 120}
        ])
    
    if not os.path.exists(EVENTS_FILE):
        save_json(EVENTS_FILE, [
            {'id': 1, 'title': 'Conférence sur l\'IA', 'description': 'Par le professeur Martin', 'date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'location': 'Amphi A', 'audience': 'Étudiants'}
        ])
    
    if not os.path.exists(MARKETPLACE_FILE):
        save_json(MARKETPLACE_FILE, [
            {'id': 1, 'title': 'Livres de maths', 'description': 'Lot de 3 livres', 'price': '15€', 'category': 'Livres', 'seller': 'Marie'}
        ])
    
    if not os.path.exists(POSTS_FILE):
        save_json(POSTS_FILE, [])
    
    if not os.path.exists(CONVERSATIONS_FILE):
        save_json(CONVERSATIONS_FILE, [])
    
    if not os.path.exists(MESSAGES_FILE):
        save_json(MESSAGES_FILE, [])
    
    if not os.path.exists(NOTIFICATIONS_FILE):
        save_json(NOTIFICATIONS_FILE, [])
    
    if not os.path.exists(RECOVERIES_FILE):
        save_json(RECOVERIES_FILE, [])
    
    if not os.path.exists(BROADCASTS_FILE):
        save_json(BROADCASTS_FILE, [])
    
    if not os.path.exists(ADS_FILE):
        save_json(ADS_FILE, [])
    
    if not os.path.exists(AUDIT_FILE):
        save_json(AUDIT_FILE, [])

def get_next_id(data):
    return max([item['id'] for item in data] + [0]) + 1

# ============================================================
# AUTH DECORATORS
# ============================================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Non authentifié'}), 401
        users = load_json(USERS_FILE)
        user = next((u for u in users if u['id'] == user_id and u['status'] == 'active'), None)
        if not user:
            return jsonify({'error': 'Compte invalide ou bloqué'}), 401
        return f(user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(user, *args, **kwargs):
        if user['role'] != 'admin':
            return jsonify({'error': 'Accès administrateur requis'}), 403
        return f(user, *args, **kwargs)
    return decorated

# ============================================================
# UTILS
# ============================================================
def create_notification(user_id, title, message, type='info'):
    notifications = load_json(NOTIFICATIONS_FILE)
    new_notif = {
        'id': get_next_id(notifications),
        'user_id': user_id,
        'title': title,
        'message': message,
        'type': type,
        'read': False,
        'created_at': datetime.utcnow().isoformat()
    }
    notifications.append(new_notif)
    save_json(NOTIFICATIONS_FILE, notifications)

def log_audit(user_id, action, message):
    logs = load_json(AUDIT_FILE)
    new_log = {
        'id': get_next_id(logs),
        'user_id': user_id,
        'action': action,
        'message': message,
        'created_at': datetime.utcnow().isoformat()
    }
    logs.append(new_log)
    save_json(AUDIT_FILE, logs)

def ensure_conversation(user1_id, user2_id):
    conversations = load_json(CONVERSATIONS_FILE)
    conv = next((c for c in conversations if (c['participant1_id'] == user1_id and c['participant2_id'] == user2_id) or (c['participant1_id'] == user2_id and c['participant2_id'] == user1_id)), None)
    if not conv:
        conv = {
            'id': get_next_id(conversations),
            'participant1_id': user1_id,
            'participant2_id': user2_id,
            'last_message': '',
            'last_message_at': datetime.utcnow().isoformat(),
            'created_at': datetime.utcnow().isoformat()
        }
        conversations.append(conv)
        save_json(CONVERSATIONS_FILE, conversations)
    return conv

# ============================================================
# ROUTES AUTH
# ============================================================
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    required = ['fullName', 'email', 'password', 'university']
    if not all(k in data for k in required):
        return jsonify({'error': 'Champs manquants'}), 400
    
    users = load_json(USERS_FILE)
    if any(u['email'] == data['email'] for u in users):
        return jsonify({'error': 'Email déjà utilisé'}), 409
    
    new_user = {
        'id': get_next_id(users),
        'uuid': str(uuid.uuid4()),
        'email': data['email'],
        'password': data['password'],
        'full_name': data['fullName'],
        'university': data['university'],
        'role': 'user',
        'status': 'active',
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    users.append(new_user)
    save_json(USERS_FILE, users)
    session['user_id'] = new_user['id']
    
    create_notification(new_user['id'], 'Bienvenue sur Campus Connect', 'Votre compte a été créé avec succès.', 'success')
    
    return jsonify({
        'id': new_user['id'],
        'uuid': new_user['uuid'],
        'email': new_user['email'],
        'fullName': new_user['full_name'],
        'university': new_user['university'],
        'role': new_user['role'],
        'status': new_user['status']
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    users = load_json(USERS_FILE)
    user = next((u for u in users if u['email'] == email and u['password'] == password), None)
    
    if not user:
        return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
    if user['status'] != 'active':
        return jsonify({'error': f'Compte {user["status"]}. Contactez l\'administration.'}), 403
    
    session['user_id'] = user['id']
    return jsonify({
        'id': user['id'],
        'uuid': user['uuid'],
        'email': user['email'],
        'fullName': user['full_name'],
        'university': user['university'],
        'role': user['role'],
        'status': user['status']
    }), 200

@app.route('/api/auth/me', methods=['GET'])
@login_required
def me(user):
    return jsonify({
        'id': user['id'],
        'uuid': user['uuid'],
        'email': user['email'],
        'fullName': user['full_name'],
        'university': user['university'],
        'role': user['role'],
        'status': user['status']
    }), 200

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'ok': True}), 200

@app.route('/api/auth/recover', methods=['POST'])
def recover():
    data = request.json
    email = data.get('email')
    req_type = data.get('type', 'password')
    message = data.get('message', '')
    
    if not email:
        return jsonify({'error': 'Email requis'}), 400
    
    recoveries = load_json(RECOVERIES_FILE)
    new_recovery = {
        'id': get_next_id(recoveries),
        'email': email,
        'request_type': req_type,
        'note': message,
        'status': 'pending',
        'temp_password': None,
        'created_at': datetime.utcnow().isoformat(),
        'resolved_at': None
    }
    recoveries.append(new_recovery)
    save_json(RECOVERIES_FILE, recoveries)
    
    return jsonify({'ok': True}), 200

# ============================================================
# ROUTES POSTS
# ============================================================
@app.route('/api/posts', methods=['GET'])
@login_required
def get_posts(user):
    posts = load_json(POSTS_FILE)
    users = load_json(USERS_FILE)
    
    for post in posts:
        author = next((u for u in users if u['id'] == post['author_id']), None)
        post['author'] = {
            'id': author['id'],
            'fullName': author['full_name'],
            'university': author['university']
        } if author else None
    
    return jsonify(posts), 200

@app.route('/api/posts', methods=['POST'])
@login_required
def create_post(user):
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Contenu requis'}), 400
    
    posts = load_json(POSTS_FILE)
    new_post = {
        'id': get_next_id(posts),
        'author_id': user['id'],
        'content': content,
        'likes': 0,
        'comments': 0,
        'shares': 0,
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    posts.append(new_post)
    save_json(POSTS_FILE, posts)
    log_audit(user['id'], 'create_post', f'Post ID {new_post["id"]} créé')
    
    return jsonify(new_post), 201

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(user, post_id):
    posts = load_json(POSTS_FILE)
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        return jsonify({'error': 'Post non trouvé'}), 404
    
    post['likes'] += 1
    save_json(POSTS_FILE, posts)
    
    if post['author_id'] != user['id']:
        create_notification(post['author_id'], 'Nouveau like', f'{user["full_name"]} a aimé votre publication.', 'like')
    
    return jsonify({'likes': post['likes']}), 200

@app.route('/api/posts/<int:post_id>/share', methods=['POST'])
@login_required
def share_post(user, post_id):
    posts = load_json(POSTS_FILE)
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        return jsonify({'error': 'Post non trouvé'}), 404
    
    post['shares'] += 1
    save_json(POSTS_FILE, posts)
    
    if post['author_id'] != user['id']:
        create_notification(post['author_id'], 'Nouveau partage', f'{user["full_name"]} a partagé votre publication.', 'share')
    
    return jsonify({'shares': post['shares']}), 200

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def comment_post(user, post_id):
    posts = load_json(POSTS_FILE)
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        return jsonify({'error': 'Post non trouvé'}), 404
    
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Commentaire vide'}), 400
    
    post['comments'] += 1
    save_json(POSTS_FILE, posts)
    
    if post['author_id'] != user['id']:
        create_notification(post['author_id'], 'Nouveau commentaire', f'{user["full_name"]} a commenté votre publication.', 'comment')
    
    return jsonify({'comments': post['comments']}), 201

# ============================================================
# ROUTES MESSAGES
# ============================================================
@app.route('/api/messages/conversations', methods=['GET'])
@login_required
def get_conversations(user):
    conversations = load_json(CONVERSATIONS_FILE)
    messages = load_json(MESSAGES_FILE)
    users = load_json(USERS_FILE)
    
    result = []
    for conv in conversations:
        if conv['participant1_id'] == user['id'] or conv['participant2_id'] == user['id']:
            other_id = conv['participant2_id'] if conv['participant1_id'] == user['id'] else conv['participant1_id']
            other = next((u for u in users if u['id'] == other_id), None)
            
            unread = len([m for m in messages if m['conversation_id'] == conv['id'] and m['sender_id'] != user['id'] and m.get('read_at') is None])
            
            result.append({
                'id': conv['id'],
                'participant': {
                    'id': other['id'],
                    'fullName': other['full_name'],
                    'university': other['university'],
                    'role': other['role']
                },
                'lastMessage': conv['last_message'],
                'unreadCount': unread,
                'updatedAt': conv['last_message_at']
            })
    
    result.sort(key=lambda x: x['updatedAt'] or '', reverse=True)
    return jsonify(result), 200

@app.route('/api/messages/conversations/<int:conv_id>/messages', methods=['GET'])
@login_required
def get_messages(user, conv_id):
    conversations = load_json(CONVERSATIONS_FILE)
    conv = next((c for c in conversations if c['id'] == conv_id), None)
    
    if not conv or (conv['participant1_id'] != user['id'] and conv['participant2_id'] != user['id']):
        return jsonify({'error': 'Non autorisé'}), 403
    
    messages = load_json(MESSAGES_FILE)
    conv_messages = [m for m in messages if m['conversation_id'] == conv_id]
    
    for msg in conv_messages:
        if msg['sender_id'] != user['id'] and msg.get('read_at') is None:
            msg['read_at'] = datetime.utcnow().isoformat()
    
    save_json(MESSAGES_FILE, messages)
    conv_messages.sort(key=lambda x: x['created_at'])
    
    return jsonify([{
        'id': m['id'],
        'senderId': m['sender_id'],
        'content': m['content'],
        'createdAt': m['created_at'],
        'readAt': m.get('read_at')
    } for m in conv_messages]), 200

@app.route('/api/messages/conversations/<int:conv_id>/messages', methods=['POST'])
@login_required
def send_message(user, conv_id):
    conversations = load_json(CONVERSATIONS_FILE)
    conv = next((c for c in conversations if c['id'] == conv_id), None)
    
    if not conv or (conv['participant1_id'] != user['id'] and conv['participant2_id'] != user['id']):
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.json
    content = data.get('content', '').strip()
    
    if not content:
        return jsonify({'error': 'Message vide'}), 400
    
    messages = load_json(MESSAGES_FILE)
    new_msg = {
        'id': get_next_id(messages),
        'conversation_id': conv_id,
        'sender_id': user['id'],
        'content': content,
        'read_at': None,
        'created_at': datetime.utcnow().isoformat()
    }
    messages.append(new_msg)
    save_json(MESSAGES_FILE, messages)
    
    conv['last_message'] = content
    conv['last_message_at'] = datetime.utcnow().isoformat()
    save_json(CONVERSATIONS_FILE, conversations)
    
    other_id = conv['participant2_id'] if conv['participant1_id'] == user['id'] else conv['participant1_id']
    create_notification(other_id, 'Nouveau message', f'{user["full_name"]} vous a envoyé un message.', 'message')
    
    return jsonify({'id': new_msg['id'], 'createdAt': new_msg['created_at']}), 201

# ============================================================
# ROUTES NOTIFICATIONS
# ============================================================
@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications(user):
    notifications = load_json(NOTIFICATIONS_FILE)
    user_notifs = [n for n in notifications if n['user_id'] == user['id']]
    user_notifs.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(user_notifs), 200

# ============================================================
# ROUTES GROUPS / EVENTS / MARKETPLACE
# ============================================================
@app.route('/api/groups', methods=['GET'])
@login_required
def get_groups(user):
    return jsonify(load_json(GROUPS_FILE)), 200

@app.route('/api/events', methods=['GET'])
@login_required
def get_events(user):
    return jsonify(load_json(EVENTS_FILE)), 200

@app.route('/api/marketplace', methods=['GET'])
@login_required
def get_marketplace(user):
    return jsonify(load_json(MARKETPLACE_FILE)), 200

# ============================================================
# ROUTES ADMIN
# ============================================================
@app.route('/api/admin/dashboard', methods=['GET'])
@login_required
@admin_required
def admin_dashboard(user):
    users = load_json(USERS_FILE)
    posts = load_json(POSTS_FILE)
    recoveries = load_json(RECOVERIES_FILE)
    audit = load_json(AUDIT_FILE)
    
    stats = {
        'totalUsers': len(users),
        'connectedUsers': 0,
        'suspendedUsers': len([u for u in users if u['status'] == 'suspended']),
        'bannedUsers': len([u for u in users if u['status'] == 'banned']),
        'pendingRecoveries': len([r for r in recoveries if r['status'] == 'pending']),
        'totalPosts': len(posts)
    }
    
    return jsonify({
        'stats': stats,
        'users': [{
            'id': u['id'],
            'uuid': u['uuid'],
            'email': u['email'],
            'fullName': u['full_name'],
            'university': u['university'],
            'role': u['role'],
            'status': u['status']
        } for u in users],
        'recoveries': recoveries,
        'posts': [{
            'id': p['id'],
            'authorName': next((u['full_name'] for u in users if u['id'] == p['author_id']), 'Inconnu'),
            'content': p['content'],
            'createdAt': p['created_at']
        } for p in posts],
        'audit': audit[-50:]
    }), 200

@app.route('/api/admin/users/<int:user_id>/status', methods=['PATCH'])
@login_required
@admin_required
def update_user_status(admin, user_id):
    users = load_json(USERS_FILE)
    target = next((u for u in users if u['id'] == user_id), None)
    
    if not target:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    new_status = request.json.get('status')
    if new_status not in ['active', 'suspended', 'banned']:
        return jsonify({'error': 'Statut invalide'}), 400
    
    target['status'] = new_status
    save_json(USERS_FILE, users)
    log_audit(admin['id'], 'update_status', f'Statut de {target["email"]} changé en {new_status}')
    create_notification(target['id'], 'Statut modifié', f'Votre statut a été mis à jour : {new_status}', 'warning')
    
    return jsonify({'ok': True}), 200

@app.route('/api/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(admin, user_id):
    users = load_json(USERS_FILE)
    target = next((u for u in users if u['id'] == user_id), None)
    
    if not target:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404
    
    temp_password = str(uuid.uuid4())[:8]
    target['password'] = temp_password
    save_json(USERS_FILE, users)
    log_audit(admin['id'], 'reset_password', f'Mot de passe réinitialisé pour {target["email"]}')
    create_notification(target['id'], 'Mot de passe réinitialisé', f'Votre mot de passe temporaire est : {temp_password}', 'info')
    
    return jsonify({'tempPassword': temp_password}), 200

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(admin, user_id):
    if user_id == admin['id']:
        return jsonify({'error': 'Vous ne pouvez pas vous supprimer vous-même'}), 400
    
    users = load_json(USERS_FILE)
    users = [u for u in users if u['id'] != user_id]
    save_json(USERS_FILE, users)
    log_audit(admin['id'], 'delete_user', f'Utilisateur {user_id} supprimé')
    
    return jsonify({'ok': True}), 200

@app.route('/api/admin/recoveries/<int:recovery_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_recovery(admin, recovery_id):
    recoveries = load_json(RECOVERIES_FILE)
    recovery = next((r for r in recoveries if r['id'] == recovery_id), None)
    
    if not recovery or recovery['status'] != 'pending':
        return jsonify({'error': 'Demande non trouvable ou déjà traitée'}), 400
    
    temp_password = str(uuid.uuid4())[:8]
    recovery['status'] = 'resolved'
    recovery['temp_password'] = temp_password
    recovery['resolved_at'] = datetime.utcnow().isoformat()
    save_json(RECOVERIES_FILE, recoveries)
    log_audit(admin['id'], 'resolve_recovery', f'Demande de récupération pour {recovery["email"]} résolue')
    
    return jsonify({'tempPassword': temp_password}), 200

@app.route('/api/admin/broadcasts', methods=['POST'])
@login_required
@admin_required
def broadcast(admin):
    data = request.json
    message = data.get('message', '').strip()
    
    if not message:
        return jsonify({'error': 'Message requis'}), 400
    
    broadcasts = load_json(BROADCASTS_FILE)
    new_broadcast = {
        'id': get_next_id(broadcasts),
        'message': message,
        'created_by': admin['id'],
        'created_at': datetime.utcnow().isoformat()
    }
    broadcasts.append(new_broadcast)
    save_json(BROADCASTS_FILE, broadcasts)
    
    users = load_json(USERS_FILE)
    for u in users:
        if u['status'] == 'active':
            create_notification(u['id'], 'Message global', message, 'broadcast')
    
    log_audit(admin['id'], 'broadcast', f'Message global envoyé : {message[:50]}...')
    return jsonify({'ok': True}), 200

@app.route('/api/admin/ads', methods=['POST'])
@login_required
@admin_required
def create_ad(admin):
    data = request.json
    title = data.get('title', '').strip()
    content = data.get('content', '').strip()
    target = data.get('targetUniversity', 'Toutes').strip()
    
    if not title or not content:
        return jsonify({'error': 'Titre et contenu requis'}), 400
    
    ads = load_json(ADS_FILE)
    new_ad = {
        'id': get_next_id(ads),
        'title': title,
        'content': content,
        'target_university': target,
        'created_by': admin['id'],
        'created_at': datetime.utcnow().isoformat()
    }
    ads.append(new_ad)
    save_json(ADS_FILE, ads)
    log_audit(admin['id'], 'create_ad', f'Publicité "{title}" créée')
    
    return jsonify({'ok': True}), 201

@app.route('/api/admin/posts/<int:post_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_post(admin, post_id):
    posts = load_json(POSTS_FILE)
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        return jsonify({'error': 'Post non trouvé'}), 404
    
    posts = [p for p in posts if p['id'] != post_id]
    save_json(POSTS_FILE, posts)
    log_audit(admin['id'], 'delete_post', f'Publication {post_id} supprimée')
    create_notification(post['author_id'], 'Publication supprimée', 'Votre publication a été supprimée par un administrateur.', 'danger')
    
    return jsonify({'ok': True}), 200

# ============================================================
# HEALTH CHECK
# ============================================================
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

# ============================================================
# INIT
# ============================================================
init_data()

# ============================================================
# RUN
# ============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
