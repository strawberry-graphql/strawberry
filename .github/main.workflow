workflow "New workflow" {
  on = "push"
  resolves = ["cclauss/GitHub-Action-for-pytest@master"]
}

action "cclauss/GitHub-Action-for-pytest@master" {
  uses = "cclauss/GitHub-Action-for-pytest@master"
  args = "pytest"
}
