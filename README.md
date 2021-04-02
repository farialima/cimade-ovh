# cimade-ovh

Page web très simple pour que les utilisateurs definissent eux-même les renvois d'appels, sur téléphonie OVH, soit sur un poste SIP, soit dans une file d'appel (déjà définie).

## Contexte

Le groupe informatique Cimade semble un peu débordée pour gérer les demandes de changement de ligne, de renvoi d’appel, etc. Donc le but est de rendre plus autonomes les groupes locaux de la Cimade, pour qu'ils gèrent leurs permanences téléphoniques eux-mêmes.

Mais faire utiliser le site d’administration OVH ( https://www.ovh.com/manager/ ) par les groupes locaux, ou même par les permanents régionaux, n’est pas simple :
-  ce site est difficile à utiliser, cela demande un apprentissage important : la UI est complexe, et il y a des petites subtilités (bugs de rafraîchissement…)
- le risque de “casser” quelque chose est important, et dans ce cas l’informatique du siège devrait réparer. Mon expérience est que comprendre que ce d’autres ont configuré (partiellement, ou sans réussir) est souvent très complexe
- il faut donner accès aux utilisateurs à ce site, ce qui n’est pas simple (voir tutorial écrit spécifiquement). Et une fois qu’ils ont cet accès, ils peuvent *voir* tous les configuration, ce qui est complexe et peut-être pas souhaitable.

Donc j’ai cherché un mécanisme plus simple d’accès. La solution adoptée est de s’assurer que les tâches _quotidiennes_ (rediriger la ligne vers un téléphone externe) peuvent être faites par les groupes locaux, et que l’informatique du siège garde le contrôle des lignes, et fait (sur demande des GLs) les grosses configurations : création de file d’attente, configuration des téléphone SIPs.

L’idée est donc l’informatique Cimade configure les lignes pour les GLs, mais n’a pas besoin de faire un suivi quotidien, ou hebdomadaire, comme c’est le cas actuellement, semble-t-il. Cela devrait permettre de gagner beaucoup d temps, et de ‘


## Description

contient :
 - `create_consumer_key.py` pour créer des clés (directement copié de https://github.com/ovh/python-ovh#3-authorize-your-application-to-access-a-customer-account )
 - `ovh-example.conf` modèle pour un `ovh.conf` avec les clés
 - `stats.py` pour collecter des statistiques -- assez basic et approximatif pour l'instant.
 - `index.py` pour configurer les redirections de lignes.
 - `index.html` comme page d'accueil.
 - `.htaccess` pour les redirections des pages
 - `requirements.txt` liste les librairies tierces (avec pip)

## Installation

Le site peut tourner sur un serveur Apache avec FastGCI et Python 3. Installer les lib tierces de `requirements.txt`. Il faut créer un fichier ‘ovh.conf” basé sur ovh-example.conf et y ajouter un ’token' générée avec create_consumer_key.py. On peut créer une ’token’ à durée de vie illimité.

## Configuration des lignes

La configuration est pour l’instant codée en dur dans le Python : dans les lignes ~250 de `index.py`, il y a du code pour Lyon (qui utilise la classe `Queue` pour une file d’attente) et du code pour Lille (qui utilise la classe `Redirection` pour une redirection Ligne -> Sip, qui lui-même peut être redirigé vers un poste externe).

Pour ajouter un groupe local, il faut donc :
- sur https://www.ovh.com/manager/ , créer une file d’attente, défini les messages voix, etc..(pour utiliser `Queue`) ; ou rediriger une ligne externe vers un poste SIP (pour utiliser `Redirect`)
- éditer index.html pour ajouter un groupe local. Il suffit de mettre un lien vers une sous-page (virtuelle, similaire à “/lyon/“ ou “/lille/“. Il faut y mettre un “/“ final.
- éditer index.py pour ajouter la configuration (dans les lignes ~250). C’est très simple si on connait un peu de Python, juste copier Lyon ou Paris

## Historique et notes retour d'expérience

J’ai passé pas mal de temps, lors du re-confinement de novembre 2020, à configurer les lignes OVH pour que des permanences Cimade de Lyon puissent être faites par différents bénévoles à différents moments, c’est à dire que le changement de renvoi d’appel, de façon automatique.

Je voulais avoir un mécanisme automatique, et non pas avoir à faire des changements manuels parce que je n’ai personnellement pas la patience pour être là à jour et heure fixe — surtout, je suis un peu dyslexique et je me trompe systématiquement sur des tâches simples). De plus, les APIs OVH - https://api.ovh.com/console/#/telephony - semblaient montrer que c’était assez simple à configurer. Peut-être, avec du recul, j’aurais dû chercher un bénévole de confiance pour le faire à la main chaque jour. Mais trouver un bénévole suffisamment patient (probablement retraité), et en même temps qui soit à l’aise avec la UI un peu pourrie de OVH aurait été probablement difficile… donc peut-être qu’automatiser est une bonne solution tout de même.

La difficulté a été, comme souvent, que OVH est très puissant, mais parfois un peu “buggy” ou tout au moins bizarre dans ses comportements. En particulier, les renvois extérieurs ne marchent bien que si ils sont définis avant le début de la période d’activité, mais surtout pas pendant. J’ai eu aussi des comportements bizarres quand il y a réellement une file d’attente…. à voir.

D'abord, j'ai mis en place fichier texte avec un format qui definissaient les permanences sur une semaine, et un cron job pour les commencer/terminer. Mais ce mécanisme demandait trop de gestion quotidiennes : les GL changent souvent.. Ce code est encore dans l’historique Git.

En attendant, les résultats :

- cela marche vraiment bien, pas besoin de présence humaine, ouf.

- il y a des complexités prévisibles avec les répondeurs, double-appel, etc. des bénévoles. La meilleur solution est de prévoir un temps de durée de sonnerie très court (10 secondes ou moins) pour que les appels passent au suivant avant que les répondeurs se mettent en route.

Il vaut mieux que les benevoles utilisent une ligne mobile que fixe : il y a souvent des problemes avec les lignes fixes.

- L’idée est aussi de collecter des statistiques sur les appels. Si OVH n’a pas de moyens direct d’en collecter (nombre d’appels abandonnés, nombre d’appel pris, durée moyenne d’attente…), me permettra d’en générer assez simplement.

- je n’ai pas configuré plusieurs lignes en même temps (avoir une “vrai” file d’attente) parce que finalement, les bénévoles n’ont pas souhaté le faire — ils ont préféré avoir une seule personne… je pense que ça marcherait (voir bug ci-dessus).

De plus, j'ai depuis decouverts que Aulnay n'utilise pas les file d'attente pour faire les renvoi, et ca marche tres bien. Il n'y a donc probablement pas besoin de file d'attente, contrairement a ce que le tutorial fourni par la Cimade national disait !! Donc on pourrait simplifier.

- il serait souhaitable que des appels soient pris par deux bénévoles à la fois (appel à trois “automatique”), en particulier pour que des bénévoles en cours de formation puissent participer aux appels, mais cela ne semble pas possible - si vous connaissez, je suis preneur (Thierry ?)

- le support ‘premium’ OVH est tout à fait bien :)

Si vous avez besoin, pour votre groupe local, de quelque aide, n’hésitez pas à me contacter
