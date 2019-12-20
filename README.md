# RGS
Python Open Source Remote Gaming Server 

This project is to create an open sourced Remote Gaming Server for use in iGaming Real Money as well as Social space. This code will capture what I've leared over the past few years. I'll start by building APIs for the various aspects of the service and then create a simple slot type game which will demonstrate how to utilize the APIs for gaming transactions. Finally I will code a sample adaptor for talking with backends in the iGaming space and how to add additional adaptors to the project.

Step 1: PRNG - the pseudo random number generator is the backbone of the entire system. Python has an excellent random number generator however most jurisidctions will not allow its use as over time it can be predicatble. So in comes the Secrets module with its Cryptographically secure PRNG which is much harder to predict over long periods of time (on Linux systems its just a wrapper around system random which utilizes hardware to generate random numbers.) Mersenne Twister is NOT used specifically because some jurisdictions don't allow its use and I wanted to be able to run in any jurisdiction.

This API will closely follow the python secrets module. For our purposes we need three main endpoints:
1. distrubution from n to m - used to calculate a random number between n upto but NOT including m.
2. weighted distrubution given an array of values and weights. For eample: [[1,500],[2,1000],[3,200],[4,700]]
3. shuffle for which I'll implement the Fisher-Yates algorithm here: https://en.wikipedia.org/wiki/Fisher%E2%80%93Yates_shuffle

I may add a few more endpoints should I add a game which requires some specific functionality.

Step 2: Server - expose a series of APIs which allow interaction with the various game stages. For my purposes this includes the following endpoints:
1. player - verify player session information with the backend and update their wallet informaiton.
2. escrow - wage funds (place them in escrow) pending the outcome of the game. On failure these funds are returned to the player.
3. result - report the games result to the backend. On success the escrowed amount is deducted from the player's balance. 
4. cancel - cancel an escrow amount which returns the funds to the player's wallet.
