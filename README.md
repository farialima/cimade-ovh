# cimade-ovh

Solution très simple pour automatiquement configurer des renvois d'appels à partir d'une file d'appel (déjà définie) sur téléphonie OVH..

contient :
 - `create_consumer_key.py` pour créer des clés (directement copié de https://github.com/ovh/python-ovh#3-authorize-your-application-to-access-a-customer-account )
 - `ovh-example.conf` modèle pour un `ovh.conf` avec les clés
 - `users-example.txt` modèle pour un `users.txt` qui défini les redirections de ligne
 - `stats.py` pour collecter des statistiques -- assez basic et approximatif pour l'instant.
 - `agents.py` pour configurer les redirections de lignes. Ne supporte pas plusieurs rappels à la fois ("vrai" file d'appel) mais devrait être facile à faire (si pas de bug OVH...)
 
