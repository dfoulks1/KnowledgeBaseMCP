# Security

Please report a vulnerability privately, not in a public issue: use GitHub's
[private vulnerability reporting](https://github.com/dfoulks1/bowerbird-mcp/security/advisories/new) for this repository.
Say what you found, how to reproduce it and which version (the release tag, or the
commit you installed). This is a personal project, so there is no response-time promise.

What counts: the tool reads and writes files only inside the knowledgebase it is pointed at.
A way to make it read or write outside that folder, to run a command, or to leak a secret it was
not asked to show is a security problem.
