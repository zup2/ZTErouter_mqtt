# ZTErouter_mqtt
Read the current router status of my A1 ZTE modem/router and send to MQTT-broker

Austria's major ISP (A1) provides ZTE routers. Those are usually fixed to IP ``10.0.0.138``.
As a major security flaw, they also come with username ``admin`` and no password ...
To override the *defaults*, you may use

* ``--gateway`` to setup the IP, but shall be prefixed by http:// or https:// to keep requests from complaining
* ``--gateway-user`` and ``--gateway-password`` to set your access credentials

## Test if everything works

* Run the following on the command line and watch the info appear on screen: ``python3 ZTErouter_mqtt.py``
* Push CTRL+C to exit

## To connect your router and a MQTT-broker that runs remotely

Added a set of command line parameters ``--mqtt-broker``, ``--mqtt-port``, ``--mqtt-user``, ``--mqtt-password``.
Using ``--mqtt-broker`` automatically activates publishing to that broker (``--mqtt-port`` defaults to ``1883``).
Depending on your setup, you might also require ``--mqtt-user``, ``--mqtt-password`` to access your broker.

The data is automatically published with their respective Ajax-ParamName as retreived by the ZTE router under common name 'Router', e.g.,

```
Router/LEDStatus Up
Router/IPAddress 91.115.224.198
Router/WorkIFMac 8c:68:c8:ad:2d:80
Router/DNS1 213.33.98.136
Router/DNS2 195.3.96.67
Router/UpTime 557409
Router/TotalUpTime 3236558
```

