```diff
- This is alpha release of the software. Use with caution. 
- You are responsible for proper management of your AWS account,
- any resources created by this software and all associated costs. 
```

# 1. Overview

Claves (from **c**ode enc**laves**) is a software for seamless management of virtual environments on AWS for code development.

The command line application can:
- create new EC2 instances with cloned CodeCommit repository
- manage IAM roles on your behalf to grant the enclave the least privileges
- list and delete previously created code enclaves

# 2. Motivation
Developers write the code on daily basis. They often work on multiple projects at the same time and are willing to try new libraries as it's essential part of their job. From information security point of view it's a real challange to protect them from emerging threats. For a long time supply-chain attacks remained in a area of theoretic attacks not feasible to perform in real world scenarios but it changes...  Both real and simulated attempts appeared recent years which prove that use of malicious dependencies is a great way to infect the last links of software development ecosystem. We can act and change our behaviour by following the rules of least privilege approach and security by isolation. Sometimes we won't be able to prevent the attack itself but we can minimise the impact.

The security objectives of Claves is to:
- allow developers create separated environment for each project they contribute
- prevent project's code (and its dependencies) from reading and modifying other projects data or developer's private data
- prevent the attacker from achieving the persistence on a system by the use of ephemeral environments

But also from general development perspective:
- create easily deployable environments to speed up the introduction of new code contributors
- use cloud capabilities to decrease build and test time when making changes to the codebase

References:
- https://portswigger.net/daily-swig/open-source-security-malicious-npm-packages-broadcast-sensitive-user-data-online
- https://nakedsecurity.sophos.com/2017/09/19/pypi-python-repository-hit-by-typosquatting-sneak-attack/

# 3. Long term goals

- Add more deployment options besides AWS EC2 (more CSP but also a local VMs/Dockers maybe?)
- Add more code provider options besides AWS CodeCommit (GitHub, etc.)
- Let Claves be used easily as the API not only command line app
- Let Claves be more customisable in terms of post-cloning configuration
- More ideas? Open an issue :)