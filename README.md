# cimade-ovh

Solution très simple pour automatiquement configurer des renvois d'appels à partir d'une file d'appel (déjà définie) sur téléphonie OVH..

## Description

contient :
 - `create_consumer_key.py` pour créer des clés (directement copié de https://github.com/ovh/python-ovh#3-authorize-your-application-to-access-a-customer-account )
 - `ovh-example.conf` modèle pour un `ovh.conf` avec les clés
 - `users-example.txt` modèle pour un `users.txt` qui défini les redirections de ligne
 - `stats.py` pour collecter des statistiques -- assez basic et approximatif pour l'instant.
 - `agents.py` pour configurer les redirections de lignes. Ne supporte pas plusieurs rappels à la fois ("vrai" file d'appel) mais devrait être facile à faire (si pas de bug OVH...)
 
## Historique et notes retour d'expérience

J’ai passé pas mal de temps, lors du re-confinement de novembre 2020, à configurer les lignes OVH pour que des permanences Cimade de Lyon puissent être faites par différents bénévoles à différents moments, c’est à dire que le changement de renvoi d’appel, de façon automatique.

Je voulais avoir un mécanisme automatique, et non pas avoir à faire des changements manuels parce que je n’ai personnellement pas la patience pour être là à jour et heure fixe — surtout, je suis un peu dyslexique et je me trompe systématiquement sur des tâches simples). De plus, les APIs OVH - https://api.ovh.com/console/#/telephony - semblaient montrer que c’était assez simple à configurer. Peut-être, avec du recul, j’aurais dû chercher un bénévole de confiance pour le faire à la main chaque jour. Mais trouver un bénévole suffisamment patient (probablement retraité), et en même temps qui soit à l’aise avec la UI un peu pourrie de OVH aurait été probablement difficile… donc peut-être qu’automatiser est une bonne solution tout de même.

La difficulté a été, comme souvent, que OVH est très puissant, mais parfois un peu “buggy” ou tout au moins bizarre dans ses comportements. En particulier, les renvois extérieurs ne marchent bien que si ils sont définis avant le début de la période d’activité, mais surtout pas pendant. J’ai eu aussi des comportements bizarres quand il y a réellement une file d’attente…. à voir.

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

