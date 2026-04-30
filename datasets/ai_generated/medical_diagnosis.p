% AI-generated: Medical diagnosis inference chain
% Status: Theorem
% Tests medical reasoning with symptom-to-condition inference through multiple hops
fof(symptom1, axiom, has_symptom(patient_1, fever)).
fof(symptom2, axiom, has_symptom(patient_1, cough)).
fof(symptom3, axiom, has_symptom(patient_1, fatigue)).
fof(symptom4, axiom, has_symptom(patient_2, chest_pain)).
fof(rule1, axiom, ! [P,S,C] : ((has_symptom(P,S) & indicates(S,C)) => possible_condition(P,C))).
fof(rule2, axiom, ! [P,C1,C2] : ((possible_condition(P,C1) & comorbidity(C1,C2)) => possible_condition(P,C2))).
fof(indicate1, axiom, indicates(fever, infection)).
fof(indicate2, axiom, indicates(cough, infection)).
fof(indicate3, axiom, indicates(fatigue, infection)).
fof(indicate4, axiom, indicates(chest_pain, cardiac)).
fof(comor1, axiom, comorbidity(infection, pneumonia)).
fof(conj1, conjecture, possible_condition(patient_1, infection)).
