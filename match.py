""" Michael Voelkel 2018-11-23 """
""" simple marriage algorithm maximizing student preferences """
""" michael.voelkel@uni-koeln.de """

import csv, argparse, random, heapq, itertools
from collections import OrderedDict

parser = argparse.ArgumentParser(description='Apply marriage algorithm to student preferences')
parser.add_argument('studentPreferencesFilename', metavar='studentPreferenceFilename', type=str,
                    help='the filename of the CSV file containing student preferences. '
                    'The file should contain a header line; the columns are student ID, preference1, preference2, ..., '
                    'where preferences are given by department ID')
parser.add_argument('departmentCapacityFilename', metavar='departmentCapacityFilename', type=str,
                    help='the filename of the CSV file containing department capacities. '
                    'The file should contain a header line; the columns are department ID, label and capacity.')
parser.add_argument('outputFilename', metavar='outputFilename', type=str,
                    help='the filename of the output CSV file containing student/department assignment. ')

args = parser.parse_args()

invalidStudents = []
studentPreferences = {}

with open(args.studentPreferencesFilename, 'r') as studentFile:
    studentReader = csv.DictReader(studentFile, delimiter=';', quotechar='"')
    for line in studentReader:
        values = list(line.values())
        values.pop(0) # remove student id
        values = list(filter(None, values)) # remove empty preferences
        if len(values) >= 3: # if student does not enter at least three preferences, he loses right to choose
            values.append('unassigned') # last preference is "unassigned"
            studentPreferences[list(line.values())[0]] = values
        else:
            if list(line.values())[0] != '':
                invalidStudents.append(list(line.values())[0])

departmentCapacities = {}
departmentLabels = {}

departmentCapacities['unassigned'] = 99999 # unassigned is not limited
departmentLabels['unassigned'] = 'unassigned'

with open(args.departmentCapacityFilename, 'r') as capacityFile:
    capacityReader = csv.DictReader(capacityFile, delimiter=';', quotechar='"')
    for line in capacityReader:
        departmentCapacities[list(line.values())[0]] = int(list(line.values())[2])
        departmentLabels[list(line.values())[0]] = list(line.values())[1]

# initialize with largest priority as 99
bestReachedPriorities = OrderedDict()
bestReachedPriorities[99] = 1
bestDepartmentStudents = []

for i in range(1, 50000):
    randomNumbers = {}

    for student, _ in studentPreferences.items():
        randomNumbers[student] = random.uniform(0, 1)

    # now, apply marriage algorithm
    departmentStudents = {k: [] for k in departmentCapacities.keys()}

    def tryPut(student, preferences, priority):
        """ try to put student into corresponding department """
        department = preferences[priority]

        departmentStudents[department].append([student, priority])

        # if department is full, we remove student with lowest priority
        if len(departmentStudents[department]) > departmentCapacities[department]:
            studentsSortedByRandomNumbers = sorted(departmentStudents[department], key=lambda x: randomNumbers[x[0]])
            studentToMove = studentsSortedByRandomNumbers[0]
            departmentStudents[department].remove(studentToMove)
            studentsCurrentPreference = studentToMove[1]
            tryPut(studentToMove[0], studentPreferences[studentToMove[0]], studentsCurrentPreference + 1)

    for student, preferences in studentPreferences.items():
        tryPut(student, preferences, 0)

    reachedPriorities = OrderedDict()

    for department, students in departmentStudents.items():
        for studentWithPriority in students:
            # what preference is this department for student?
            if department == 'unassigned':
                preference = 99
            else:
                preference = studentWithPriority[1]
            reachedPriorities[preference] = reachedPriorities.get(preference, 0) + 1

    optimalWorstGroup = max(bestReachedPriorities.keys())
    currentWorstGroup = max(reachedPriorities.keys())

    if (optimalWorstGroup > currentWorstGroup or optimalWorstGroup == currentWorstGroup and
        bestReachedPriorities[currentWorstGroup] > reachedPriorities[currentWorstGroup]):
        bestReachedPriorities = reachedPriorities
        bestDepartmentStudents = departmentStudents

sum = 0

for priority, numbers in sorted(bestReachedPriorities.items()):
    if priority == 99:
        priority = 'U'
    sum += numbers
    print("Prio " + str(priority + 1) + ":\t" + str(numbers) + "\tCumul.%: " + str(100. * sum / len(studentPreferences)))

# prepare csv output
# each department gets two lines, one containing students, the other one the respective priority of the student
result = []

for student in invalidStudents:
    bestDepartmentStudents['unassigned'].append([student, 99])
    # set preference "20" to unassigned students
    studentPreferences[student] = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,'unassigned']

for department, students in bestDepartmentStudents.items():
    # sort students first by priority
    students.sort(key = lambda studentWithPriority: studentWithPriority[1])
    resultRow1 = [department, 'Capacity: ', 'Students: ', 'Student']
    resultRow2 = [departmentLabels[department], departmentCapacities[department], len(students), 'Priority']

    for studentWithPriority in students:
        resultRow1.append(studentWithPriority[0])
        # in output, preference starts at 1, not 0
        resultRow2.append(studentWithPriority[1] + 1)

    result.append(resultRow1)
    result.append(resultRow2)

# transpose results
result = list(map(list, itertools.zip_longest(*result)))

csvWriter = csv.writer(open(args.outputFilename, 'w'), delimiter=';', quotechar='"')
csvWriter.writerows(result)
