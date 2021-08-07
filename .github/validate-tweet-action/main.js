const core = require('@actions/core');
const twitter = require('twitter-text')

const tweetEncoded = core.getInput('tweet');

const buff = Buffer.from(tweetEncoded, "base64");
const tweet = buff.toString("ascii");

const result = twitter.parseTweet(tweet);

if (!result.valid) {
    core.setFailed(`Tweet is not valid!`);
}
