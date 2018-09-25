# -*- coding: utf-8 -*-
"""
Created on Sun Sep 23 15:06:40 2018

@author: Paulo Augusto
"""
from ltspy import SimData
import threading
import subprocess
import random
import os
import numpy as np
import decimal

gen=0
max_gen=500
tam_pop=10
uid=0
data_filename = 'transistor.asc'
vectorial_mutation_chance=1
chance_mut=50
taxa_mut = 0.00390626
taxa_mut_max=1
taxa_mut_mult=4
taxa_mut_min=0.0001
wanted_value=430*pow(10,-9)

def to_power(unit,reverse=False):
    
    dic={'MEG':pow(10,6),
         'k':pow(10,3),
         'm':pow(10,-3),
         'u':pow(10,-6),
         'n':pow(10,-9),
         'p':pow(10,-12),
         'f':pow(10,-15),
         ' ' :1}
    dicv={pow(10,6):'MEG',
          pow(10,3):'k',
          pow(10,-3):'m',
          pow(10,-6):'u',
          pow(10,-9):'n',
          pow(10,-12):'p',
          pow(10,-15):'f',
          1:' '}
    
    if not reverse:     
        if not unit in dic:
            return 0
        return dic[unit]
    else:
        if not unit in dicv:
            return 0
        returndicv[unit]
def get_asc_data(filename):
    dic={}
    with open(filename,'r') as data_file:
        data = data_file.readlines()
        for line in data:
            if line[0:4]=='TEXT':
                begin,end=0,0
                for i in range(0,len(line)):
                    if line[i]=='(':
                        begin=i
                    if line[i]==')':
                        end=i
                parameters=line[begin+1:end]
                parameters=parameters.split(' ')
                break
    for param in parameters:
        name,number=param.split('=')
        if number==' ' or number=='-':
            continue
        for i in range(0,len(number)):
            if not ord(number[i]) in range(45,58):
                power=to_power(number[i:])
                number=number[:i]
                break
            if i == len(number)-1:
                power=1
                break

        if not power:
            continue
        dic[name]=float(number)*power
    
    return begin,end,dic

def substitute_value(arq,params,values,out):
    flag=True
    with open(arq,'r') as data:
        text=data.readlines()
        words=''
        for line in text:
            if line.find('model')>0 and flag:      
                seed=line
                for param,value in zip(params,values):
                    wordstemp=''
                    temp=seed.split(' ' + param + '=')
                    wordstemp+=temp[0]+' ' + param + '='
                    wordstemp+=value
                    temp=temp[1]
                    ind=temp.index(' ')
                    wordstemp+=temp[ind:]
                    seed=wordstemp
                words+=seed
                flag=False
            else:
                words+=line
    with open(out,'w') as out_data:
        out_data.write(words)
        
    return words
               
        
class individual():
    def __init__(self):
        global uid
        self.name=str(uid)
        uid+=1
        self.cromo=[decimal.Decimal(random.random()),decimal.Decimal(random.random())]
        self.fit=0
    def fitness(self):
        substitute_value(data_filename,
                         ['W','L'],
                         [self.cromo[0].to_eng_string(),decimal.Decimal((float(self.cromo[1])*pow(10,-6))).to_eng_string()],
                          self.name+'.asc')
        subprocess.call(['XVIIx64.exe','-b','-Run',self.name+'.asc'])
#        os.system('XVIIx64.exe -b -Run '+self.name+'.asc')
        count=0
        while not ''+self.name+'.raw' in os.listdir('.'):
            count+=1
            if count==100:
                count=0
                subprocess.call(['XVIIx64.exe','-b','-Run',self.name+'.asc'])
#                os.system('XVIIx64.exe -b -Run '+self.name+'.asc')

        data=SimData(self.name+'.raw')
        index=data.variables.index('V(vout)')
        values=data.values[index]
        vdd=sum(values[0:5])/5
        for i in range(0,len(values)):
            if values[i]<=vdd/2:
                break
        temp = data.values[0][i]
        return np.log(1/abs(wanted_value-temp))
    def evaluate(self):
        self.fit=self.fitness()
            
    
        
class population():
    def __init__(self,tam_pop):
        self.population=[individual() for i in range(0,tam_pop)]
    def dump_files(self):
        extensions=['log','op.raw','raw','asc','net']
        threads=[]
        def dump(indiv):
            temp='del '
            for ext in extensions:
                temp+= indiv.name+'.'+ext+' '
            os.system(temp)
        for indiv in self.population:
            threads.append(threading.Thread(target=dump,args=(indiv,)))
#        for j in range(0,len(self.population)/4+1):
#            subthreads=threads[j*4:(j+1)*4]
        [thread.start() for thread in threads]
        [thread.join()  for thread in threads]
        del threads
#            subprocess.call(['del',indiv.name+'.log'])
#            subprocess.call(['del',indiv.name+'.raw'])
#            subprocess.call(['del',indiv.name+'.op.raw'])
#            subprocess.call(['del',indiv.name+'.net'])
#    
    def evaluateAll(self):
        threads=[]
        for i in range(0,len(self.population)):
            threads.append(threading.Thread(target=self.population[i].evaluate))
#            threads[-1].start()
#            self.population[i].evaluate()
#        for j in range(0,len(self.population)/4+1):
#            subthreads=threads[j*4:(j+1)*4]
        [thread.start() for thread in threads]
        [thread.join()  for thread in threads]
        del threads
        self.dump_files()
def mean_crossover(pais):
    son=individual()
    son.cromo=[sum([pai.cromo[0] for pai in pais])/len(pais),
               sum([pai.cromo[1] for pai in pais])/len(pais)]
    mutate(son)
    return son
def mutate(indiv):

    global taxa_mut,chance_mut
    
    if random.random()<vectorial_mutation_chance:
        temp=[random.random(),random.random()]
        amp=np.sqrt(sum([pow(i,2) for i in temp]))
        temp=[value*taxa_mut/amp for value in temp]
        indiv.cromo=[decimal.Decimal(temp[i])+indiv.cromo[i] for i in range(0,len(indiv.cromo))]
    else:
        temp=[]
        for i in range(0,len(indiv.cromo)):
            if chance_mut<random.random()*100:
                mut=(2*random.random()-1)*taxa_mut
    #            temp.append(decimal.Decimal(mut+float(value)))
                indiv.cromo[i]+=decimal.Decimal(mut)
    
    for i in range(0,len(indiv.cromo)):
        if indiv.cromo[i]<=0:
            indiv.cromo[i]=0.005
def torneio(pop):
    best=pop.population[0]
    for ind in pop.population:
        if ind.fit>best.fit:
            best=ind
    return best

def generate_pop(best,pop):
    for i in range(0,len(pop.population)):
        if not pop.population[i]==best:
            pop.population[i]=mean_crossover([pop.population[i],best])
    
    
class populationControl():
    global  tam_pop,\
            taxa_mut,\
            chance_mut,\
            max_gen,\
            taxa_mut,\
            taxa_mutMax,\
            taxa_mut_mult,\
            taxa_mut_min

    def __init__(self):
        self._taxa_mut=taxa_mut
        self._chance_mut=chance_mut
        self._max_gen=max_gen
        self._tam_pop=tam_pop            
        self._taxa_mut_min=taxa_mut_min
        self._taxa_mut_max=taxa_mut_max
        self._taxa_mut_mult=taxa_mut_mult
        self._counter=0
        self._expansion=False
  
    def control(self,gen,best,last):
        global taxa_mut
#        taxa_mut=self._taxa_mutMax
        ascending_counter=0
        if gen>25:
            if best.fit<=last.fit*1.001: #If the fitness doesnt grow by 0.1%
                self._counter+=1
            else:
    #            taxa_mut=self._taxa_mut
                chanceMut=self._chanceMut
                self._expansion=False
                self._counter=0
                ascending_counter=0
                
            
            if self._counter==10:    # If the fitness doesnt grow in n generations
                if self._expansion: # If it the taxa_mut is increasing 
                    if taxa_mut<self._taxa_mut_max:    # If taxa_mut is less than the maximum
                        taxa_mut*=self._taxa_mut_mult

                    else:           # If taxa_mut bigger than the maximum
                        self._expansion=False
    
                else:               # If taxa_mut is decreasing
                    if taxa_mut>self._taxa_mut_min:    # If it is bigger than the minimum
                        taxa_mut/=self._taxa_mut_mult
                    else:                           # If it is less than the minimum
                        self._expansion=True    
                
                self._counter=0  
                
def remove_suckers(pop,n):
    
    def getFit(indiv):
        return indiv.fit
    pop.population.sort(reverse=False,key=getFit)
    for i in range(0,n):
        pop.population[i]=individual()
        pop.population[i].evaluate()
def clean_workspace():
    archives=os.listdir('.')
    extensions=['log','raw','asc','net']
    arqs=''
    for archive in archives:
        if (archive[-3:] in extensions) and (not archive == 'transistor.asc'):
            arqs+=archive+' '
#    print arqs
    threading.Thread(target=os.system,args=('del '+arqs,)).start()

def main():
    gen=0
    global pop,alltimebest
    pop=population(tam_pop)
    controller=populationControl()
    last=pop.population[0]
    while gen<max_gen:
        gen+=1
        pop.evaluateAll()
        remove_suckers(pop,tam_pop/5)
        print [a.fit for a in pop.population]
        best = torneio(pop)
        generate_pop(best,pop)
        controller.control(gen,best,last)
        last=best    
        alltimebest=[best.cromo[0],best.cromo[1]]
        print best.fit,best.name,gen,taxa_mut
        

                