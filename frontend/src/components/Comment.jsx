import React, { useState } from 'react';

const Comment = ({ comment, postId, currentUser, onLike, onUnlike, onReply }) => {
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replyContent, setReplyContent] = useState('');

  const handleReply = async (e) => {
    e.preventDefault();
    if (!replyContent.trim()) return;

    await onReply(comment.id, replyContent);
    setReplyContent('');
    setShowReplyForm(false);
  };

  return (
    <div className={`ml-${comment.depth * 4} mb-3`}>
      <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full flex items-center justify-center text-white font-bold text-sm">
                {comment.author.charAt(0).toUpperCase()}
              </div>
              <span className="font-semibold text-gray-800">{comment.author}</span>
              <span className="text-gray-500 text-sm">
                {new Date(comment.created_at).toLocaleDateString()}
              </span>
            </div>
            <p className="text-gray-700 mb-3">{comment.content}</p>
            <div className="flex items-center gap-4">
              <button
                onClick={() => onLike(comment.id)}
                className="flex items-center gap-1 text-sm text-gray-600 hover:text-red-500 transition"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" />
                </svg>
                <span className="font-medium">{comment.like_count}</span>
              </button>
              <button
                onClick={() => setShowReplyForm(!showReplyForm)}
                className="text-sm text-blue-600 hover:text-blue-700 font-medium"
              >
                Reply
              </button>
            </div>
          </div>
        </div>

        {showReplyForm && (
          <form onSubmit={handleReply} className="mt-3 pt-3 border-t border-gray-200">
            <textarea
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              placeholder="Write your reply..."
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows="2"
            />
            <div className="flex gap-2 mt-2">
              <button
                type="submit"
                className="px-4 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
              >
                Reply
              </button>
              <button
                type="button"
                onClick={() => setShowReplyForm(false)}
                className="px-4 py-1 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        )}
      </div>

      {/* Render nested replies */}
      {comment.replies && comment.replies.length > 0 && (
        <div className="mt-2">
          {comment.replies.map((reply) => (
            <Comment
              key={reply.id}
              comment={reply}
              postId={postId}
              currentUser={currentUser}
              onLike={onLike}
              onUnlike={onUnlike}
              onReply={onReply}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default Comment;
