'''
Created on Jul 13, 2016

@author: Gus
'''
class Player():
    def __init__(self):
        self.__health = 100
        
    def takeDamage(self, damage):
        self.__health = self.__health - damage;
        
    def healthPickUp(self):
        
        if self.__health < 50:
            self.__health = self.health + 50
        else:
            self.__health = 100
            
    def getHealth(self):
        return self.__health