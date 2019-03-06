# edgesim

## Mininet Installation

```
git clone https://github.com/mininet/mininet.git

# Follow the instructions in the INSTALL document
# in short

cd mininet
git checkout 2.2.2
sudo util/install.sh -fnv

# Verify that mininet works with
sudo mn --test pingall
sudo mn -c
```

## Running edgesim

The edgesim master is a server that creates the network over mininet
and responds to http requests to change a device's link to a tower.

Start the edgesim master server as follows - 

```
sudo python -m edgesim.master.server
```

Once the master brings up the network, either use xterms to access the
device and the registry.

To bring up the registry,

```
python -m edgesim.registry.server
```

To run the client,

```
python -m edgesim.client.main
```
