# Isolated security lab — planned

No vulnerable application is implemented in this milestone.

The first exercise will be IDOR with fictional accounts and entries. Its own
Compose project must use a private network, disposable database/storage, localhost
ports, and fake credentials. Never mount production environment files, private-data,
backup folders, Docker socket, or real cloud credentials. Never connect the lab to
production networks. Start one exercise at a time.

Each finding must record identifier, severity, reproduction, expected/actual
behavior, root cause, fix, and regression test. Later exercises can cover the
remaining topics in the project README.
