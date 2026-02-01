import React, { useState } from 'react';
import { commentAPI } from '../services/api';
import Comment from './Comment';

const Post = ({ post, currentUser, onLike, onUnlike, onUpdate }) => {
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState([]);
  const [showCommentForm, setShowCommentForm] = useState(false);
  const [commentContent, setCommentContent] = useState('');
  const [loading, setLoading] = useState(false);

  const loadComments = async () => {
    if (!showComments) {
      setLoading(true);
      try {
        // Fetch the post with comments
        const response = await fetch(`http://localhost:8000/api/posts/${post.id}/`);
        const data = await response.json();
        setComments(data.comments || []);
        setShowComments(true);
      } catch (error) {
        console.error('Error loading comments:', error);
      } finally {
        setLoading(false);
      }
    } else {
      setShowComments(false);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!commentContent.trim()) return;

    try {
      const newComment = await commentAPI.create({
        post: post.id,
        author: currentUser,
        content: commentContent,
      });
      setCommentContent('');
      setShowCommentForm(false);
      // Reload comments to get the full tree
      const response = await fetch(`http://localhost:8000/api/posts/${post.id}/`);
      const data = await response.json();
      setComments(data.comments || []);
      // Update parent component's post list
      onUpdate();
    } catch (error) {
      console.error('Error adding comment:', error);
    }
  };

  const handleCommentLike = async (commentId) => {
    try {
      const response = await commentAPI.like(commentId, currentUser);
      // Update comment like count in the tree
      const updateCommentLikes = (commentsList) => {
        return commentsList.map(comment => {
          if (comment.id === commentId) {
            return { ...comment, like_count: response.data.like_count };
          }
          if (comment.replies && comment.replies.length > 0) {
            return { ...comment, replies: updateCommentLikes(comment.replies) };
          }
          return comment;
        });
      };
      setComments(updateCommentLikes(comments));
    } catch (error) {
      console.error('Error liking comment:', error);
      if (error.response?.data?.error) {
        alert(error.response.data.error);
      }
    }
  };

  const handleReply = async (parentId, content) => {
    try {
      await commentAPI.create({
        post: post.id,
        parent: parentId,
        author: currentUser,
        content: content,
      });
      // Reload comments to get the updated tree
      const response = await fetch(`http://localhost:8000/api/posts/${post.id}/`);
      const data = await response.json();
      setComments(data.comments || []);
      // Update parent to reflect new comment count
      onUpdate();
    } catch (error) {
      console.error('Error adding reply:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
            {post.author.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="font-bold text-gray-800">{post.author}</h3>
            <p className="text-sm text-gray-500">
              {new Date(post.created_at).toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
              })}
            </p>
          </div>
        </div>
      </div>

      <p className="text-gray-700 mb-4 text-lg leading-relaxed">{post.content}</p>

      <div className="flex items-center gap-6 pt-4 border-t border-gray-200">
        <button
          onClick={() => onLike(post.id)}
          className="flex items-center gap-2 text-gray-600 hover:text-red-500 transition font-medium"
        >
          <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
            <path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" />
          </svg>
          <span>{post.like_count} Likes</span>
        </button>

        <button
          onClick={loadComments}
          className="flex items-center gap-2 text-gray-600 hover:text-blue-500 transition font-medium"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z"
            />
          </svg>
          <span>{post.comment_count || 0} Comments</span>
        </button>

        <button
          onClick={() => setShowCommentForm(!showCommentForm)}
          className="text-blue-600 hover:text-blue-700 font-medium ml-auto"
        >
          Add Comment
        </button>
      </div>

      {showCommentForm && (
        <form onSubmit={handleAddComment} className="mt-4 pt-4 border-t border-gray-200">
          <textarea
            value={commentContent}
            onChange={(e) => setCommentContent(e.target.value)}
            placeholder="What are your thoughts?"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows="3"
          />
          <div className="flex gap-2 mt-2">
            <button
              type="submit"
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Post Comment
            </button>
            <button
              type="button"
              onClick={() => setShowCommentForm(false)}
              className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 font-medium"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {showComments && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          {loading ? (
            <p className="text-gray-500 text-center">Loading comments...</p>
          ) : comments.length > 0 ? (
            <div className="space-y-2">
              {comments.map((comment) => (
                <Comment
                  key={comment.id}
                  comment={comment}
                  postId={post.id}
                  currentUser={currentUser}
                  onLike={handleCommentLike}
                  onReply={handleReply}
                />
              ))}
            </div>
          ) : (
            <p className="text-gray-500 text-center">No comments yet. Be the first to comment!</p>
          )}
        </div>
      )}
    </div>
  );
};

export default Post;
