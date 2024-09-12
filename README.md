# quiz_bot
This bot can be used for quiz channel without polls (only posts)

Commands:
/reset - Reset all points from users
/top <count> - Displaying the rating of players included in the top <count>

How it works:
1. Admin posted puzzle
2. Users answer in discussion under the post
3. If anyone write correct(cheating) answer admin reply his message and write anything with +points or -points (without spaces)
4. Bot handling reply by admin and try to found +points or -points in message
5. If bot found it - writes the result to the database and if not - doing nothing

If you promote anyone to admin, bot handling it by yourself and writes his ID on database
All records in score database include ID@username and points
