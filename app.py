import os
import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, request, jsonify, session, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from sqlalchemy import func, text

# ------------------------- CONFIGURATION -------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'campus-connect-secret-key-2026-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Jeremie322K%3F@db.tpntjwffektufspmarow.supabase.co:5432/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)

# Extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
CORS(app, supports_credentials=True, origins=['http://localhost:5000', 'http://localhost:3000', 'https://*', '*'])

# ------------------------- MODÈLES -------------------------
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    university = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, with_email=True):
        data = {
            'id': self.id,
            'uuid': self.uuid,
            'fullName': self.full_name,
            'university': self.university,
            'role': self.role,
            'status': self.status,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }
        if with_email:
            data['email'] = self.email
        return data

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    likes = db.Column(db.Integer, default=0)
    comments = db.Column(db.Integer, default=0)
    shares = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    author = db.relationship('User', backref='posts')

    def to_dict(self):
        return {
            'id': self.id,
            'author': {
                'id': self.author.id,
                'fullName': self.author.full_name,
                'university': self.author.university
            },
            'content': self.content,
            'likes': self.likes,
            'comments': self.comments,
            'shares': self.shares,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.relationship('User')

class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_like'),)

class Share(db.Model):
    __tablename__ = 'shares'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('post_id', 'user_id', name='unique_share'),)

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.Integer, primary_key=True)
    participant1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    participant2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    last_message = db.Column(db.Text, default='')
    last_message_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    participant1 = db.relationship('User', foreign_keys=[participant1_id])
    participant2 = db.relationship('User', foreign_keys=[participant2_id])

    def other_participant(self, user_id):
        return self.participant2 if self.participant1_id == user_id else self.participant1

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User')

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read = db.Column(db.Boolean, default=False)
    user = db.relationship('User')

class RecoveryRequest(db.Model):
    __tablename__ = 'recovery_requests'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=False)
    request_type = db.Column(db.String(50), nullable=False)
    note = db.Column(db.Text, default='')
    status = db.Column(db.String(50), default='pending')
    temp_password = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

class Broadcast(db.Model):
    __tablename__ = 'broadcasts'
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Ad(db.Model):
    __tablename__ = 'ads'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    target_university = db.Column(db.String(255), default='Toutes')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------------- AUTH DECORATOR -------------------------
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Non authentifié'}), 401
        user = User.query.get(user_id)
        if not user or user.status != 'active':
            return jsonify({'error': 'Compte invalide ou bloqué'}), 401
        return f(user, *args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(user, *args, **kwargs):
        if user.role != 'admin':
            return jsonify({'error': 'Accès administrateur requis'}), 403
        return f(user, *args, **kwargs)
    return decorated

# ------------------------- UTILS -------------------------
def create_notification(user_id, title, message, type='info'):
    notif = Notification(user_id=user_id, title=title, message=message, type=type)
    db.session.add(notif)
    db.session.commit()

def log_audit(user_id, action, message):
    log = AuditLog(user_id=user_id, action=action, message=message)
    db.session.add(log)
    db.session.commit()

def ensure_conversation(user1_id, user2_id):
    conv = Conversation.query.filter(
        ((Conversation.participant1_id == user1_id) & (Conversation.participant2_id == user2_id)) |
        ((Conversation.participant1_id == user2_id) & (Conversation.participant2_id == user1_id))
    ).first()
    if not conv:
        conv = Conversation(participant1_id=user1_id, participant2_id=user2_id)
        db.session.add(conv)
        db.session.commit()
    return conv

# ------------------------- ROUTES AUTH -------------------------
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    required = ['fullName', 'email', 'password', 'university']
    if not all(k in data for k in required):
        return jsonify({'error': 'Champs manquants'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email déjà utilisé'}), 409
    hashed = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(
        email=data['email'],
        password_hash=hashed,
        full_name=data['fullName'],
        university=data['university'],
        role='user',
        status='active'
    )
    db.session.add(user)
    db.session.commit()
    session['user_id'] = user.id
    create_notification(user.id, 'Bienvenue sur Campus Connect', 'Votre compte a été créé avec succès.', 'success')
    return jsonify(user.to_dict()), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
    if user.status != 'active':
        return jsonify({'error': f'Compte {user.status}. Contactez l\'administration.'}), 403
    session['user_id'] = user.id
    return jsonify(user.to_dict()), 200

@app.route('/api/auth/me', methods=['GET'])
@login_required
def me(user):
    return jsonify(user.to_dict()), 200

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
    recovery = RecoveryRequest(email=email, request_type=req_type, note=message)
    db.session.add(recovery)
    db.session.commit()
    return jsonify({'ok': True}), 200

# ------------------------- ROUTES POSTS -------------------------
@app.route('/api/posts', methods=['GET'])
@login_required
def get_posts(user):
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return jsonify([p.to_dict() for p in posts]), 200

@app.route('/api/posts', methods=['POST'])
@login_required
def create_post(user):
    data = request.json
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Contenu requis'}), 400
    post = Post(author_id=user.id, content=content)
    db.session.add(post)
    db.session.commit()
    log_audit(user.id, 'create_post', f'Post ID {post.id} créé')
    return jsonify(post.to_dict()), 201

@app.route('/api/posts/<int:post_id>/like', methods=['POST'])
@login_required
def like_post(user, post_id):
    post = Post.query.get_or_404(post_id)
    existing = Like.query.filter_by(post_id=post_id, user_id=user.id).first()
    if existing:
        return jsonify({'error': 'Déjà aimé'}), 409
    like = Like(post_id=post_id, user_id=user.id)
    db.session.add(like)
    post.likes += 1
    db.session.commit()
    if post.author_id != user.id:
        create_notification(post.author_id, 'Nouveau like', f'{user.full_name} a aimé votre publication.', 'like')
    return jsonify({'likes': post.likes}), 200

@app.route('/api/posts/<int:post_id>/share', methods=['POST'])
@login_required
def share_post(user, post_id):
    post = Post.query.get_or_404(post_id)
    existing = Share.query.filter_by(post_id=post_id, user_id=user.id).first()
    if existing:
        return jsonify({'error': 'Déjà partagé'}), 409
    share = Share(post_id=post_id, user_id=user.id)
    db.session.add(share)
    post.shares += 1
    db.session.commit()
    if post.author_id != user.id:
        create_notification(post.author_id, 'Nouveau partage', f'{user.full_name} a partagé votre publication.', 'share')
    return jsonify({'shares': post.shares}), 200

@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
@login_required
def comment_post(user, post_id):
    post = Post.query.get_or_404(post_id)
    data = request.json
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Commentaire vide'}), 400
    comment = Comment(post_id=post_id, author_id=user.id, content=content)
    db.session.add(comment)
    post.comments += 1
    db.session.commit()
    if post.author_id != user.id:
        create_notification(post.author_id, 'Nouveau commentaire', f'{user.full_name} a commenté votre publication.', 'comment')
    return jsonify({'comments': post.comments}), 201

# ------------------------- ROUTES MESSAGES -------------------------
@app.route('/api/messages/conversations', methods=['GET'])
@login_required
def get_conversations(user):
    convs = Conversation.query.filter(
        (Conversation.participant1_id == user.id) | (Conversation.participant2_id == user.id)
    ).order_by(Conversation.last_message_at.desc()).all()
    result = []
    for conv in convs:
        other = conv.other_participant(user.id)
        unread = Message.query.filter(
            Message.conversation_id == conv.id,
            Message.sender_id != user.id,
            Message.read_at.is_(None)
        ).count()
        result.append({
            'id': conv.id,
            'participant': {
                'id': other.id,
                'fullName': other.full_name,
                'university': other.university,
                'role': other.role
            },
            'lastMessage': conv.last_message,
            'unreadCount': unread,
            'updatedAt': conv.last_message_at.isoformat() if conv.last_message_at else None
        })
    return jsonify(result), 200

@app.route('/api/messages/conversations/<int:conv_id>/messages', methods=['GET'])
@login_required
def get_messages(user, conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    if conv.participant1_id != user.id and conv.participant2_id != user.id:
        return jsonify({'error': 'Non autorisé'}), 403
    Message.query.filter(
        Message.conversation_id == conv_id,
        Message.sender_id != user.id,
        Message.read_at.is_(None)
    ).update({'read_at': datetime.utcnow()})
    db.session.commit()
    messages = Message.query.filter_by(conversation_id=conv_id).order_by(Message.created_at.asc()).all()
    return jsonify([{
        'id': m.id,
        'senderId': m.sender_id,
        'content': m.content,
        'createdAt': m.created_at.isoformat(),
        'readAt': m.read_at.isoformat() if m.read_at else None
    } for m in messages]), 200

@app.route('/api/messages/conversations/<int:conv_id>/messages', methods=['POST'])
@login_required
def send_message(user, conv_id):
    conv = Conversation.query.get_or_404(conv_id)
    if conv.participant1_id != user.id and conv.participant2_id != user.id:
        return jsonify({'error': 'Non autorisé'}), 403
    data = request.json
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'error': 'Message vide'}), 400
    msg = Message(conversation_id=conv_id, sender_id=user.id, content=content)
    db.session.add(msg)
    conv.last_message = content
    conv.last_message_at = datetime.utcnow()
    db.session.commit()
    other_id = conv.participant1_id if conv.participant2_id == user.id else conv.participant2_id
    create_notification(other_id, 'Nouveau message', f'{user.full_name} vous a envoyé un message.', 'message')
    return jsonify({'id': msg.id, 'createdAt': msg.created_at.isoformat()}), 201

# ------------------------- ROUTES NOTIFICATIONS -------------------------
@app.route('/api/notifications', methods=['GET'])
@login_required
def get_notifications(user):
    notifs = Notification.query.filter_by(user_id=user.id).order_by(Notification.created_at.desc()).all()
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.type,
        'createdAt': n.created_at.isoformat(),
        'read': n.read
    } for n in notifs]), 200

# ------------------------- ROUTES GROUPS / EVENTS / MARKETPLACE -------------------------
GROUPS = [
    {'id': 1, 'title': 'Club Informatique', 'description': 'Échange sur les technologies', 'tag': 'Tech', 'members': 45},
    {'id': 2, 'title': 'Bibliothèque', 'description': 'Partage de ressources', 'tag': 'Académique', 'members': 120}
]
EVENTS = [
    {'id': 1, 'title': 'Conférence sur l\'IA', 'description': 'Par le professeur Martin', 'date': (datetime.utcnow() + timedelta(days=7)).isoformat(), 'location': 'Amphi A', 'audience': 'Étudiants'}
]
MARKETPLACE = [
    {'id': 1, 'title': 'Livres de maths', 'description': 'Lot de 3 livres', 'price': '15€', 'category': 'Livres', 'seller': 'Marie'}
]

@app.route('/api/groups', methods=['GET'])
@login_required
def get_groups(user):
    return jsonify(GROUPS), 200

@app.route('/api/events', methods=['GET'])
@login_required
def get_events(user):
    return jsonify(EVENTS), 200

@app.route('/api/marketplace', methods=['GET'])
@login_required
def get_marketplace(user):
    return jsonify(MARKETPLACE), 200

# ------------------------- ROUTES ADMIN -------------------------
@app.route('/api/admin/dashboard', methods=['GET'])
@login_required
@admin_required
def admin_dashboard(user):
    stats = {
        'totalUsers': User.query.count(),
        'connectedUsers': 0,
        'suspendedUsers': User.query.filter_by(status='suspended').count(),
        'bannedUsers': User.query.filter_by(status='banned').count(),
        'pendingRecoveries': RecoveryRequest.query.filter_by(status='pending').count(),
        'totalPosts': Post.query.count()
    }
    users = User.query.all()
    recoveries = RecoveryRequest.query.order_by(RecoveryRequest.created_at.desc()).all()
    posts = Post.query.order_by(Post.created_at.desc()).all()
    audit = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(50).all()
    return jsonify({
        'stats': stats,
        'users': [u.to_dict() for u in users],
        'recoveries': [{
            'id': r.id,
            'email': r.email,
            'requestType': r.request_type,
            'note': r.note,
            'status': r.status,
            'tempPassword': r.temp_password,
            'createdAt': r.created_at.isoformat()
        } for r in recoveries],
        'posts': [{'id': p.id, 'authorName': p.author.full_name, 'content': p.content, 'createdAt': p.created_at.isoformat()} for p in posts],
        'audit': [{'action': a.action, 'message': a.message, 'createdAt': a.created_at.isoformat()} for a in audit]
    }), 200

@app.route('/api/admin/users/<int:user_id>/status', methods=['PATCH'])
@login_required
@admin_required
def update_user_status(admin, user_id):
    target = User.query.get_or_404(user_id)
    new_status = request.json.get('status')
    if new_status not in ['active', 'suspended', 'banned']:
        return jsonify({'error': 'Statut invalide'}), 400
    target.status = new_status
    db.session.commit()
    log_audit(admin.id, 'update_status', f'Statut de {target.email} changé en {new_status}')
    create_notification(target.id, 'Statut modifié', f'Votre statut a été mis à jour : {new_status}', 'warning')
    return jsonify({'ok': True}), 200

@app.route('/api/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_password(admin, user_id):
    target = User.query.get_or_404(user_id)
    temp_password = str(uuid.uuid4())[:8]
    hashed = bcrypt.generate_password_hash(temp_password).decode('utf-8')
    target.password_hash = hashed
    db.session.commit()
    log_audit(admin.id, 'reset_password', f'Mot de passe réinitialisé pour {target.email}')
    create_notification(target.id, 'Mot de passe réinitialisé', f'Votre mot de passe temporaire est : {temp_password}', 'info')
    return jsonify({'tempPassword': temp_password}), 200

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(admin, user_id):
    target = User.query.get_or_404(user_id)
    if target.id == admin.id:
        return jsonify({'error': 'Vous ne pouvez pas vous supprimer vous-même'}), 400
    db.session.delete(target)
    db.session.commit()
    log_audit(admin.id, 'delete_user', f'Utilisateur {target.email} supprimé')
    return jsonify({'ok': True}), 200

@app.route('/api/admin/recoveries/<int:recovery_id>/resolve', methods=['POST'])
@login_required
@admin_required
def resolve_recovery(admin, recovery_id):
    recovery = RecoveryRequest.query.get_or_404(recovery_id)
    if recovery.status != 'pending':
        return jsonify({'error': 'Déjà traité'}), 400
    temp_password = str(uuid.uuid4())[:8]
    recovery.status = 'resolved'
    recovery.temp_password = temp_password
    recovery.resolved_at = datetime.utcnow()
    db.session.commit()
    log_audit(admin.id, 'resolve_recovery', f'Demande de récupération pour {recovery.email} résolue')
    return jsonify({'tempPassword': temp_password}), 200

@app.route('/api/admin/broadcasts', methods=['POST'])
@login_required
@admin_required
def broadcast(admin):
    data = request.json
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'error': 'Message requis'}), 400
    broadcast = Broadcast(message=message, created_by=admin.id)
    db.session.add(broadcast)
    users = User.query.filter_by(status='active').all()
    for u in users:
        create_notification(u.id, 'Message global', message, 'broadcast')
    db.session.commit()
    log_audit(admin.id, 'broadcast', f'Message global envoyé : {message[:50]}...')
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
    ad = Ad(title=title, content=content, target_university=target, created_by=admin.id)
    db.session.add(ad)
    db.session.commit()
    log_audit(admin.id, 'create_ad', f'Publicité "{title}" créée')
    return jsonify({'ok': True}), 201

@app.route('/api/admin/posts/<int:post_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_post(admin, post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    log_audit(admin.id, 'delete_post', f'Publication {post_id} supprimée')
    create_notification(post.author_id, 'Publication supprimée', 'Votre publication a été supprimée par un administrateur.', 'danger')
    return jsonify({'ok': True}), 200

# ------------------------- HEALTH CHECK -------------------------
@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

# ------------------------- INIT DB -------------------------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(role='admin').first():
        hashed = bcrypt.generate_password_hash('Admin@2026').decode('utf-8')
        admin = User(
            email='admin@campusconnect.app',
            password_hash=hashed,
            full_name='Administrateur Principal',
            university='Campus Central',
            role='admin',
            status='active'
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin par défaut créé : admin@campusconnect.app / Admin@2026")

# ------------------------- RUN -------------------------
if __name__ == '__main__':
    port = 5000
    app.run(host='0.0.0.0', port=port, debug=False)
