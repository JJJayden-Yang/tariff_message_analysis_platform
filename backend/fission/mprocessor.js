/**
 * Transforms raw Mastodon post data into standardized format
 * @async
 * @param {Object} context - Fission execution context
 * @returns {Object} Processed response
 * @property {number} status - HTTP status code
 * @property {string} body - JSON string of processed observations
 */
module.exports = async function(context) {
    const extractEntities = (content, type) => {
        const regex = type === 'hashtags' ? /#(\w+)/g : /@(\w+)/g;
        const matches = content.match(regex);
        return matches ? Array.from(new Set(matches)) : [];
    };
    try {
        const postData = context.request.body;
        
        return {
            status: 200,
            body: JSON.stringify({
                metadata: {
                    post_id: postData.post_id,
                    created_time: postData.created_time,
                    url: postData.url,
                    language: postData.language,
                    region: postData.region,
                    processed_at: new Date().toISOString()
                },
                author: {
                    acct: postData.author.acct,
                    display_name: postData.author.display_name || postData.author.acct,
                    profile_url: postData.author.url,
                    domain: postData.author.Domain,
                    join_date: postData.author.created_time
                },
                content: {
                    text: postData.content,
                    hashtags: extractEntities(postData.content, 'hashtags'),
                    mentions: extractEntities(postData.content, 'mentions'),
                    word_count: postData.content.split(/\s+/).length
                },
                engagement: {
                    favorites: postData.favourited_by || [],
                    reblogs: postData.reblogged_by || [],
                    replies: postData.replies || []
                },
            }, null, 2)
        };
    } catch (error) {
        console.error('Processing failed:', error);
        return {
            status: 500,
            body: JSON.stringify({
                error: 'Failed to process post',
                details: error.message
            })
        };
    }
};