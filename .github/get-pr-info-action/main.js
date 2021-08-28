const core = require("@actions/core");
const github = require("@actions/github");

const run = async () => {
  const { ACCESS_TOKEN } = process.env;

  if (!ACCESS_TOKEN) {
    return core.setFailed("Missing ACCESS_TOKEN");
  }

  let username = "";

  const { payload, sha, eventName } = github.context;
  const octokit = github.getOctokit(ACCESS_TOKEN);

  if (eventName === "pull_request" || eventName === "pull_request_target") {
    username = github.context.payload.pull_request.user.login;
  } else {
    const { repository } = payload;

    const {
      data: [pullRequest],
    } = await octokit.rest.repos.listPullRequestsAssociatedWithCommit({
      owner: repository.owner.login,
      repo: repository.name,
      commit_sha: sha,
    });

    if (!pullRequest) {
      console.log("no pull request found for this commit");
      return;
    }

    const contributor = pullRequest.user;
    username = pullRequest.user.login;
  }
  const { data: author } = await octokit.rest.users.getByUsername({
    username,
  });

  const name = author.name || author.login;

  core.setOutput("contributor-name", name);
  core.setOutput("contributor-username", author.login);
};

run();
