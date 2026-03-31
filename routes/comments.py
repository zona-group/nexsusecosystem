from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Comment, CommentLike
from datetime import datetime

comments = Blueprint('comments', __name__)

@comments.route('/api/comments/<article_id>')
def get_comments(article_id):
    page = int(request.args.get('page', 1))
    per_page = 20
    query = Comment.query.filter_by(
        article_id=article_id,
        is_deleted=False,
        parent_id=None
    ).order_by(Comment.created_at.desc())
    total = query.count()
    items = query.offset((page-1)*per_page).limit(per_page).all()

    result = []
    for c in items:
        liked = False
        if current_user.is_authenticated:
            liked = CommentLike.query.filter_by(
                user_id=current_user.id, comment_id=c.id
            ).first() is not None

        replies_data = []
        for r in c.replies.filter_by(is_deleted=False).order_by(Comment.created_at.asc()).all():
            replies_data.append({
                'id':       r.id,
                'content':  r.content,
                'author':   r.author.username,
                'avatar':   r.author.avatar,
                'likes':    r.like_count(),
                'created':  r.created_at.strftime('%Y-%m-%d %H:%M'),
            })

        result.append({
            'id':       c.id,
            'content':  c.content,
            'author':   c.author.username,
            'avatar':   c.author.avatar,
            'likes':    c.like_count(),
            'liked':    liked,
            'created':  c.created_at.strftime('%Y-%m-%d %H:%M'),
            'replies':  replies_data,
        })

    return jsonify({'comments': result, 'total': total, 'page': page})


@comments.route('/api/comments/<article_id>', methods=['POST'])
@login_required
def post_comment(article_id):
    data = request.get_json()
    content   = data.get('content','').strip()
    parent_id = data.get('parent_id', None)

    if not content or len(content) < 2:
        return jsonify({'error': 'Comment too short.'}), 400
    if len(content) > 1000:
        return jsonify({'error': 'Comment too long (max 1000 chars).'}), 400

    comment = Comment(
        article_id=article_id,
        user_id=current_user.id,
        content=content,
        parent_id=parent_id
    )
    db.session.add(comment)
    db.session.commit()

    return jsonify({
        'id':      comment.id,
        'content': comment.content,
        'author':  current_user.username,
        'avatar':  current_user.avatar,
        'likes':   0,
        'liked':   False,
        'created': comment.created_at.strftime('%Y-%m-%d %H:%M'),
        'replies': [],
    }), 201


@comments.route('/api/comments/<int:comment_id>/like', methods=['POST'])
@login_required
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    existing = CommentLike.query.filter_by(
        user_id=current_user.id, comment_id=comment_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        return jsonify({'liked': False, 'likes': comment.like_count()})
    else:
        like = CommentLike(user_id=current_user.id, comment_id=comment_id)
        db.session.add(like)
        db.session.commit()
        return jsonify({'liked': True, 'likes': comment.like_count()})


@comments.route('/api/comments/<int:comment_id>', methods=['DELETE'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    comment.is_deleted = True
    db.session.commit()
    return jsonify({'success': True})
