# Custom Nagios Plugins

This repo contains a bunch of Nagios plugins that I wrote.
You're welcome to use them.

## Docker Debugging

There's a dockerfile present in `assets/python_remote_debug` for debugging inside a docker container.

You can build it with:

```
docker build -t python_remote --file "assets/python_remote_debug/Dockerfile" .
```

and you can run it with:

```
docker run -it -d -p 2022:22 -v ${HOME}/.ssh/id_rsa.pub:/root/.ssh/authorized_keys:ro --rm --name python_remote python_remote:latest
```

you can then ssh into the container:

```
ssh -p 2022 root@localhost
```

You can use python remote debugging to connect your debugger to the running instance
