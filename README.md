# cimade-ovh

Ce projet est une toute petite app web, en fait une page web très simple, pour que les utilisateurs definissent eux-même les renvois d'appels, sur téléphonie OVH, soit sur un poste SIP, soit dans une file d'appel (à définir auparavant sur le site d'administration OVH).

## Contexte

Le groupe informatique Cimade semble un peu débordé pour gérer les demandes de changement de ligne, de renvoi d’appel, etc. Donc le but est de rendre plus autonomes les groupes locaux de la Cimade, pour qu'ils gèrent leurs permanences téléphoniques eux-mêmes.

Mais faire utiliser le site d’administration OVH ( https://www.ovh.com/manager/ ) par les groupes locaux, ou même par les permanents régionaux, n’est pas simple :
- Ce site est difficile à utiliser, cela demande un apprentissage important : la UI est complexe, et il y a des petites subtilités (bugs de rafraîchissement…). 
- Le risque de “casser” quelque chose est important, et dans ce cas l’informatique du siège devrait réparer. Mon expérience est que comprendre que ce d’autres ont configuré (partiellement, ou sans réussir) est souvent très complexe.
- Il faut donner accès aux utilisateurs à ce site, ce qui n’est pas simple (voir tutorial écrit spécifiquement). Et une fois qu’ils ont cet accès, ils peuvent *voir* tous les configuration, ce qui est complexe et peut-être pas souhaitable.

Donner accès aux groupes locaux à l'interface OVH donnerait, je pense, beaucoup de travail au groupe informatique : il faudrait trouver les bons "administrateurs" locaux ou régionaux qui ne seront pas rebutés par le site d'administration OVH ; les former ; compléter les tutoriaux ; et leur fournir du support. Je pense donc que ce n'est pas une bonne solution.

Donc j’ai cherché un mécanisme plus simple. La solution que j'ai implimentée essaie d’assurer que les tâches _quotidiennes_ (rediriger la ligne vers un téléphone externe) peuvent être faites par les groupes locaux, et que l’informatique du siège garde le contrôle des lignes, et fait (sur demande des GLs) les grosses configurations : création de file d’attente, configuration des téléphone SIPs. Donc l’informatique Cimade n’a pas besoin de faire un suivi quotidien, ou hebdomadaire, comme c’est le cas actuellement, semble-t-il. Cela devrait permettre de gagner beaucoup de temps ; et cela veut dire qu'il y a moins besoin, pour l'instant, de completer des tutoriaux sur comment et de laisser les régions ou les GLs acceder au site d'administration OVH.

## Description

Le projet contient :
 - `create_consumer_key.py` pour créer des clés (directement copié de https://github.com/ovh/python-ovh#3-authorize-your-application-to-access-a-customer-account )
 - `ovh-example.conf` modèle pour un `ovh.conf` avec les clés
 - `stats.py` pour collecter des statistiques. completement basic et approximatif pour l'instant. Hardcodé pour Lyon. Je le fais tourner comme un cron job toutes les 5 minutes pendant les permanences. Aucun outil d'analyse, juste au cas où. 
 - `index.py` tout le code de la page web
 - `.htaccess` pour les redirections des pages
 - `requirements.txt` liste les librairies tierces (avec pip)

## Installation

Le site peut tourner sur un serveur Apache 2 avec mod_rewrite et FastGCI, et Python 3.

Pour installer :
- creer un virtualenv dans `./.venv3`
- installer les lib tierces avec `source .venv3/bin/activate ; pip install -r requirements.txt`
- créer un fichier `ovh.conf` basé sur `ovh-example.conf` et y ajouter un ’token' générée avec `create_consumer_key.py`. On peut créer une ’token’ à durée de vie illimité.

## Configuration des lignes

La configuration est pour l’instant codée en dur dans le Python : dans les lignes ~250 de `index.py`, il y a du code pour Lyon (qui utilise la classe `Queue` pour une file d’attente) et du code pour Lille (qui utilise la classe `Redirection` pour une redirection Ligne -> Sip, qui lui-même peut être redirigé vers un poste externe).

Pour ajouter un groupe local, il faut donc :
- sur https://www.ovh.com/manager/ , créer une file d’attente, défini les messages voix, etc..(pour utiliser `Queue`) ; ou rediriger une ligne externe vers un poste SIP (pour utiliser `Redirect`)
- éditer index.py pour ajouter la configuration (dans les lignes ~250). C’est très simple si on connait un peu de Python, juste copier Lyon ou Lille. Ajouter aussi, dans le HTML pour la page d'accueil (un peu plus bas dans le code), un lien vers une sous-page (virtuelle), similaire à “/lyon“ ou “/lille“.

## Historique

J’ai passé pas mal de temps, lors du re-confinement de novembre 2020, à configurer les lignes OVH pour que des permanences Cimade de Lyon puissent être faites par différents bénévoles à différents moments, c’est à dire que le changement de renvoi d’appel, de façon automatique.

Je voulais avoir un mécanisme automatique, et non pas avoir à faire des changements manuels parce que je n’ai personnellement pas la patience pour être là à jour et heure fixe — surtout, je suis un peu dyslexique et je me trompe systématiquement sur des tâches simples). De plus, les APIs OVH - https://api.ovh.com/console/#/telephony - semblaient montrer que c’était assez simple à configurer. Peut-être, avec du recul, j’aurais dû chercher un bénévole de confiance pour le faire à la main chaque jour. Mais trouver un bénévole suffisamment patient (probablement retraité), et en même temps qui soit à l’aise avec la UI un peu pourrie de OVH aurait été probablement difficile… donc peut-être qu’automatiser est une bonne solution tout de même.

La difficulté a été, comme souvent, que OVH est très puissant, mais parfois un peu “buggy” ou tout au moins bizarre dans ses comportements. En particulier, les renvois extérieurs ne marchent bien que si ils sont définis avant le début de la période d’activité, mais surtout pas pendant. J’ai eu aussi des comportements bizarres quand il y a réellement une file d’attente…. à voir.

D'abord, j'ai mis en place fichier texte avec un format qui definissaient les permanences sur une semaine, et un cron job pour les commencer/terminer. Mais ce mécanisme demandait trop de gestion quotidiennes : les GL changent souvent. Ce code est encore dans l’historique Git.

# Conclusions / problemes / bugs / perspectives

- Cela marche vraiment bien (testé par deux groupes locaux). Pas de bug connus.

- Il y a des complexités prévisibles avec les répondeurs, double-appel, etc. des bénévoles, quand on utilise une file d'appel. La meilleur solution est de prévoir un temps de durée de sonnerie très court (10 secondes ou moins) pour que les appels passent au suivant avant que les répondeurs se mettent en route.

En particulier, Il vaut mieux que les benevoles utilisent une ligne mobile que fixe : il y a souvent des problemes avec les lignes fixes.

- Il est important d'enregistrer des messages d'accueil, de débordement, ... surtout quand on utilise une file d'appel. Sinon les gens ne comprennent pas.

- je n’ai pas implémenté la possibilité d'avoir plusieurs bénévoles qui répondent en même temps, chacun à un appel (plusieurs lignes en même temps). Lyon n’a pas souhaité l'avoir,  ils ont préféré avoir une seule personne ; Lille en a parlé, ils en auront peut-être le besoin. Ce serait facile à ajouter (c'est presque plus la UI qui demandera du travail - gérer plusieurs champs "telephone")

- pour que les appels soient pris par deux bénévoles à la fois (appel à trois “automatique”), en particulier pour que des bénévoles en cours de formation puissent participer aux appels, une solution qui marche : 
  * faire une file d'appel, pour que les appels soient transmis un-par-un
  * faire une conférence ; ca n'est pas possible avec OVH il semble, mais c'est facile par exemple sur Twillio (il faut acheter un numéro mais c'est quelques euros par mois ; et ensuite définir un "TwiML Bin" qui contiennent juste la connection à une conférence :
```
<?xml version="1.0" encoding="UTF-8"?><Response><Dial><Conference>Permanence Cimade</Conference></Dial></Response>
```
(Voir la doc sur https://www.twilio.com/docs/voice/twiml/conference et https://www.twilio.com/docs/voice/api/conference-resource )

Cela marche, on s'en est servi : la seule complexité est qu'il faut que les gens qui appellent racrochent eux-mêmes, pour que l'appel suivant soit transmis. Et aussi, il est transmis immediatement, donc pas de pause :). 

- le support ‘premium’ OVH est vraiment bien -- ça vaut le coup de les appeler, même si on attend très longtemps, parfois plusieurs heures, ils savent bien les choses et prennent le temps de répondre. C'est souvent mieux que mettre un ticket de support.

