# https://raw.githubusercontent.com/TemporalAgent7/datacore-bot/master/src/DataCore.Library/Utils/VoyageCalculator.cs

import random
import math
import PlayerData


def time_format(duration):
    hours = math.floor(duration)
    minutes = math.floor((duration - hours) * 60)
    return "{}h {}m".format(hours, minutes)


def voyage_estimator_simple(ps, ss, o1, o2, o3, o4, startAm, debug=False): #, numExtends=2, currentAm=0, elapsedHours=0):
    if min(ps, ss, o1, o2, o3, o4, startAm) <= 0:
        raise Exception('invalid parameters')

    if debug:
        print("{} {} {} {} {} {} {}".format(ps, ss, o1, o2, o3, o4, startAm)) #, numExtends, currentAm, elapsedHours))

    amPerHour = 1260

    profVariance = 20 / 100
    aveLuck = 0.5       # pass a 50% check 50% of the time
    safeLuck = 0.1      # pass a 50% check 10% of the time
    saferLuck = 0.01    # pass a 50% check 1% of the time
    aveProf = 1 + profVariance * aveLuck
    safeProf = 1 + profVariance * safeLuck
    saferProf = 1 + profVariance * saferLuck
    psChance = 0.35
    ssChance = 0.25
    osChance = 0.1
    skills = [ps, ss, o1, o2, o3, o4]

    for skill in skills:
        assert type(skill) is int and skill >= 0, skill
    assert type(startAm) is int and startAm >= 0
#        assert type(currentAm) is int and currentAm >= 0
#        assert type(elapsedHours) in [int,float] and elapsedHours >=0

#        if currentAm > 0 and elapsedHours > 0:
#            am = currentAm
#            elapsed = elapsedHours
#        else:
#            am = startAm
#            elapsed = 0
    am = startAm
#        elapsed = 0

    estimates = []
    for prof in [aveProf, safeProf, saferProf]:
        estimate = 0
        for iSkill in range(len(skills)):
            skill = skills[iSkill]
            if iSkill == 0:
                chance = psChance
            elif iSkill == 1:
                chance = ssChance
            else:
                chance = osChance

            if debug:
                print('{} * {} / {} * {} = {}'.format(skill, prof, amPerHour, chance, skill * prof / amPerHour * chance))
            estimate += skill * prof / amPerHour * chance
        if debug:
            print('{} / {} = {}'.format(am, amPerHour, am / amPerHour))
        estimate += am / amPerHour
        if debug:
            print("{} = {}".format(estimate, SimpleVoyageEstimator.__time_format(estimate)))
        estimates.append(estimate)

    if debug:
        print("Voyage has a {:0.0f}% chance of {}, a {:0.0f}% chance of {}, and a {:0.0f}% chance of {}.".format(
            (1-aveLuck)*100,
            time_format(estimates[0]),
            (1-safeLuck)*100,
            time_format(estimates[1]),
            (1-saferLuck)*100,
            time_format(estimates[2])))

    return estimates


def ratio_optimizer():

    class Swaps:
        __pairs = None
        __starting_state = None

        def __init__(self):
            if self.__starting_state is not None:
                self.__pairs = self.__starting_state
                return

            self.__pairs = set()
            for i in range(6):
                for j in range (6):
                    if i == j:
                        continue
                    self.__pairs.add((i,j))

            self.__starting_state = self.__pairs.copy()

        def __str__(self):
            return str(sorted(self.__pairs))

        def __len__(self):
            return len(self.__pairs)

        def __iter__(self):
            return self.__pairs.__iter__()

        def __contains__(self, item):
            return self.__pairs.__iter__()

        def pop(self):
            return self.__pairs.pop()

        def reset(self):
            self.__pairs = self.__starting_state.copy()

        def remove(self, pair):
            self.__pairs.remove(pair)

    skills = [7333] * 6
    startAm = 2700

    maxRounds = 100
    startIncrement = 1000
    incrementFactor = 10
    increment = startIncrement
    swaps = Swaps()
    lastEstimate, lastSafeEstimate, lastSaferEstimate = voyage_estimator_simple(*skills, startAm)
    for iRound in range(maxRounds):
        while len(swaps) > 0:
            pair = swaps.pop()
            if skills[pair[1]] < increment:
                continue
            skills[pair[0]] += increment
            skills[pair[1]] -= increment

            estimate, safeEstimate, saferEstimate = voyage_estimator_simple(*skills, startAm)
            diff = estimate - lastEstimate
            print("{:4d} {:0.3f} {:0.3f} {:0.3f}".format(iRound, estimate, safeEstimate, saferEstimate), skills,
                  "change of {:0.3f}".format(diff), "{} swaps left".format(len(swaps)))

            if diff > 0:
                lastEstimate, lastSafeEstimate, lastSaferEstimate = estimate, safeEstimate, saferEstimate
                swaps.reset()
                break
            else:
                estimate, safeEstimate, saferEstimate = lastEstimate, lastSafeEstimate, lastSaferEstimate
                skills[pair[0]] -= increment
                skills[pair[1]] += increment

#            if increment == 1 or increment == int(increment/incrementFactor):
#                print('Done!')
#                break
#            print('Reducing increment from {} to {}'.format(increment, increment/incrementFactor))
#            increment = int(increment/incrementFactor)
        swaps.reset()


class VoyageResult:

    def __init__(self):
        self.result = None
        self.safeResult = None
        self.saferResult = None
        self.lastDil = None
        self.dilChance = None
        self.refillCostResult = None

    def __str__(self):
        # Estimated voyage length of {TimeFormat(extendResults[0].result)}
        #    {extendResults[0].dilChance}% chance to reach the {extendResults[0].lastDil}hr dilemma;
        #    refill with {extendResults[1].refillCostResult} dil for a {extendResults[1].dilChance}%
        #    chance to reach the {extendResults[1].lastDil}hr dilemma.

        template = 'Estimated voyage length of {} (99% worst case {}).  {}% chance to reach the {}hr dilemma; ' \
                    'refill with {} dil for a {}% chance to reach the {}hr dilemma.'
        return template.format(time_format(self.result),
                               time_format(self.saferResult),
                               self.dilChance,
                               99,
                               self.lastDil,
                               10,
                               88)


def voyage_calculator2(ps, ss, o1, o2, o3, o4, startAm, numExtends=2, currentAm=0, elapsedHours=0):
    '''
    Description
    :param ps: Primary skill total
    :param ss: Secondary skill total
    :param o1: Other skill 1 total
    :param o2: Other skill 2 total
    :param o3: Other skill 3 total
    :param o4: Other skill 4 total
    :param startAm: Starting AM (antimatter)
    :param numExtends: Number of voyage extends to calculate (?)
    :param currentAm: Current AM (antimatter)
    :param elapsedHours: Elapsed time in the voyage so far
    :return: tuple of (VoyageResults[], n20hrdil, n20hrrefills)
    '''

    if min(ps, ss, o1, o2, o3, o4, startAm) <= 0:
        raise Exception('invalid parameters')

    # Config settings
    numSims = 5000   # must be >= 100
    maxExtends = 100
    maxNum20hourSims = 100

    # Constants
    secondsPerTick = 20
    secondsInMinute = 60
    minutesInHour = 60
    hazardTick = 4
    rewardTick = 7
    hazardAsRewardTick = 28
    ticksPerMinute = secondsInMinute / secondsPerTick
    ticksPerHour = ticksPerMinute * minutesInHour
    amPerActivity = 1
    hoursBetweenDilemmas = 2
    ticksBetweenDilemmas = hoursBetweenDilemmas * minutesInHour * ticksPerMinute
    hazSkillPerHour = 1260
    hazSkillPerTick = hazSkillPerHour / ticksPerHour
    hazAmPass = 5
    hazAmFail = 30
    psChance = 0.35
    ssChance = 0.25
    dilPerMin = 5

    # Unused constants
    # ticksPerCycle = 28
    # cycleSeconds = ticksPerCycle * secondsPerTick
    # cyclesPerHour = minutesInHour * secondsInMinute / cycleSeconds
    # hazPerCycle = 6
    # activityPerCycle = 18
    # dilemmasPerHour = 1 / hoursBetweenDilemmas
    # hazPerHour = hazPerCycle * cyclesPerHour - dilemmasPerHour
    # activityAmPerHour = activityPerCycle * cyclesPerHour * amPerActivity
    # osChance = 0.1
    # skillChances = [psChance, ssChance, osChance, osChance, osChance, osChance]
    # currentAm = 0

    # Initialize starting values
    if currentAm > 0:
        ship = currentAm
    else:
        ship = startAm

    num20hourSims = min([maxNum20hourSims, numSims])

    # Proficiency: this might slightly refine estimates in some cases but most users can ignore this.
    # It's the % of your average proficiency roll relative to your average total roll -
    # increase if using gauntlet crew)
    hazSkillVariance = 20 / 100
    skills = [ps, ss, o1, o2, o3, o4]

    results = [[0] * (numSims+1)] * (numExtends+1)
    resultsRefillCostTotal = [0] * (numExtends+1)

    results20hrCostTotal = 0
    results20hrRefillsTotal = 0

    for iSim in range(numSims):
        tick = math.floor(elapsedHours * ticksPerHour)
        am = ship
        refillCostTotal = 0
        extend = 0

        while True:
            tick += 1
            # sanity escape:
            if tick == 10000:
                break

            # hazard && not dilemma
            if (tick % hazardTick == 0) and (tick % hazardAsRewardTick != 0) and (tick % ticksBetweenDilemmas != 0):
                hazDiff = tick * hazSkillPerTick

                # pick the skill
                skillPickRoll = random.random()
                if skillPickRoll < psChance:
                    skill = ps
                elif skillPickRoll < psChance + ssChance:
                    skill = ss
                else:
                    skill = skills[2 + random.randint(0, 3)]  # 2,3,4,5

                # check (roll if necessary)
                skillVar = hazSkillVariance * skill
                skillMin = skill - skillVar
                if hazDiff < skillMin:
                    # automatic success
                    am += hazAmPass
                else:
                    skillMax = skill + skillVar
                    if hazDiff >= skillMax:
                        # automatic fail
                        am -= hazAmFail
                    else:
                        # roll for it
                        skillRoll = random.randint(skillMin, skillMax)
                        # test.text += minSkill + "-" + maxSkill + "=" + skillRoll + " "
                        if skillRoll >= hazDiff:
                            am += hazAmPass
                        else:
                            am -= hazAmFail

            elif (tick % rewardTick != 0) and (tick % hazardAsRewardTick != 0) and\
                    (tick % ticksBetweenDilemmas != 0):
                am -= amPerActivity

            if am <= 0:
                # system failure
                if extend == maxExtends:
                    break

                voyTime = tick / ticksPerHour
                refillCost = math.ceil(voyTime * 60 / dilPerMin)

                if extend <= numExtends:
                    results[extend][iSim] = tick / ticksPerHour
                    if extend > 0:
                        resultsRefillCostTotal[extend] += refillCostTotal

                am = startAm
                refillCostTotal += refillCost
                extend += 1

                if voyTime > 20:
                    results20hrCostTotal += refillCostTotal
                    results20hrRefillsTotal += extend
                    break

                if (extend > numExtends) and (iSim >= num20hourSims):
                    break

    # List<ExtendResult> extendResults = new List<ExtendResult>()
    voyageResults = []
    for extend in range(numExtends+1):
        exResults = results[extend]

        # TODO: ascending or descending?
        exResults.sort(reverse=False)
        voyTime = exResults[math.floor(len(exResults) / 2)]

        # compute other results
        safeTime = exResults[math.floor((len(exResults) / 10))]
        saferTime = exResults[math.floor((len(exResults) / 100))]
        # safestTime = exResults[0]

        # compute last dilemma chance
        lastDilemma = 0
        lastDilemmaFails = 0
        for i in range(len(exResults)):
            dilemma = math.floor(exResults[i] / hoursBetweenDilemmas)
            if dilemma > lastDilemma:
                lastDilemma = dilemma
                lastDilemmaFails = max(0, i)

        dilChance = round((100 * (len(exResults) - lastDilemmaFails) / len(exResults)))
        # HACK: if there is a tiny chance of the next dilemma, assume 100% chance of the previous one instead
        assert type(dilChance) is int
        if dilChance == 0:
            lastDilemma -= 1
            dilChance = 100

        extendResult = VoyageResult()
        extendResult.result = voyTime
        extendResult.safeResult = safeTime
        extendResult.saferResult = saferTime
        extendResult.lastDil = lastDilemma * hoursBetweenDilemmas
        extendResult.dilChance = dilChance
        extendResult.refillCostResult = math.ceil(resultsRefillCostTotal[extend] / numSims) if extend > 0 else 0
        voyageResults.append(extendResult)

        # the threshold here is just a guess
        '''
        if maxSkill / hazSkillPerHour > voyTime:
            tp = math.floor(voyTime * hazSkillPerHour)
            if currentAm == 0:
                # setWarning(extend, "Your highest skill is too high by about " +
                #       Math.floor(maxSkill - voyTime * hazSkillPerHour) +
                #       ". To maximize voyage time, redistribute more like this: " +
                #       tp + "/" + tp + "/" + tp / 4 + "/" + tp / 4 + "/" + tp / 4 + "/" + tp / 4 + ".");
                pass
        '''

    # 20 hour cost (dil) = Math.ceil(results20hrCostTotal / num20hourSims);
    # for this many refills = Math.round(results20hrRefillsTotal / num20hourSims);
    n20hrdil = math.ceil(results20hrCostTotal / num20hourSims)
    n20hrrefills = round(results20hrRefillsTotal / num20hourSims)

    return voyageResults, n20hrdil, n20hrrefills


def voyage_calculator_cs(ps, ss, o1, o2, o3, o4, startAm, elapsedHours=0):

    numSims = 5000

    numExtends = 2
    maxExtends = 100
    maxNum20hourSims = 100
    # ticksPerCycle = 28
    secondsPerTick = 20
    secondsInMinute = 60
    minutesInHour = 60
    hazardTick = 4
    rewardTick = 7
    hazardAsRewardTick = 28
    ticksPerMinute = secondsInMinute / secondsPerTick
    ticksPerHour = ticksPerMinute * minutesInHour
    # cycleSeconds = ticksPerCycle * secondsPerTick
    # cyclesPerHour = minutesInHour * secondsInMinute / cycleSeconds
    # hazPerCycle = 6
    amPerActivity = 1
    # activityPerCycle = 18
    hoursBetweenDilemmas = 2
    # dilemmasPerHour = 1 / hoursBetweenDilemmas
    ticksBetweenDilemmas = hoursBetweenDilemmas * minutesInHour * ticksPerMinute
    # hazPerHour = hazPerCycle * cyclesPerHour - dilemmasPerHour
    hazSkillPerHour = 1260
    hazSkillPerTick = hazSkillPerHour / ticksPerHour
    hazAmPass = 5
    hazAmFail = 30
    # activityAmPerHour = activityPerCycle * cyclesPerHour * amPerActivity
    psChance = 0.35
    ssChance = 0.25
    # osChance = 0.1

    # skillChances = [psChance, ssChance, osChance, osChance, osChance, osChance]
    dilPerMin = 5

    hazSkillance = 20 / 100

    # currentAm = 0
    ship = startAm

    num20hourSims = min([maxNum20hourSims, numSims])

    # elapsedHazSkill = elapsedHours * hazSkillPerHour

    skills = [ps, ss, o1, o2, o3, o4]
    # maxSkill = float(max([0, max(skills) - elapsedHazSkill]))
    # endVoySkill = maxSkill * (1 + hazSkillance)

    '''
    results = new List<List<double>>()
    resultsRefillCostTotal = new List<double>()
    for iExtend in range(numExtends+1):
        resultsEntry = new List<double>(numSims)
        for i in range(numSims+1):
            resultsEntry.Add(0)
        results.Add(resultsEntry)
        resultsRefillCostTotal.Add(0)
    '''
    # results = [[0 for i in range(numSims+1)] for j in range(numExtends+1)]
    results = [[0] * (numSims+1)] * (numExtends+1)
    # resultsRefillCostTotal = [0 for i in range(numExtends+1)]
    resultsRefillCostTotal = [0] * (numExtends+1)

    results20hrCostTotal = 0
    results20hrRefillsTotal = 0

    for iSim in range(numSims):
        tick = math.floor(elapsedHours * ticksPerHour)
        am = ship
        refillCostTotal = 0
        extend = 0

        while True:
            tick += 1
            # sanity escape:
            if tick == 10000:
                break

            # hazard && not dilemma
            if (tick % hazardTick == 0) and (tick % hazardAsRewardTick != 0) and (tick % ticksBetweenDilemmas != 0):
                hazDiff = tick * hazSkillPerTick

                # pick the skill
                skillPickRoll = random.random()
                if skillPickRoll < psChance:
                    skill = ps
                elif skillPickRoll < psChance + ssChance:
                    skill = ss
                else:
                    # C# code: skill = skills[2 + RND.Next(0, 3)]
                    # -- RND.Next is exclusive of max value, but random.randint is inclusive
                    # skill = skills[2 + random.randint(0, 2)]  <-- this was a bug, should have been (0, 3)
                    skill = skills[2 + random.randint(0, 3)]

                # check (roll if necessary)
                skillVar = hazSkillance * skill
                skillMin = skill - skillVar
                if hazDiff < skillMin:
                    # automatic success
                    am += hazAmPass
                else:
                    skillMax = skill + skillVar
                    if hazDiff >= skillMax:
                        # automatic fail
                        am -= hazAmFail
                    else:
                        # roll for it
                        # skillRoll = RND.Next(skillMin, skillMax)
                        # -- RND.Next is exclusive of max value, but random.randint is inclusive
                        skillRoll = random.randint(skillMin, skillMax-1)
                        # test.text += minSkill + "-" + maxSkill + "=" + skillRoll + " "
                        if skillRoll >= hazDiff:
                            am += hazAmPass
                        else:
                            am -= hazAmFail

            elif (tick % rewardTick != 0) and (tick % hazardAsRewardTick != 0) and\
                    (tick % ticksBetweenDilemmas != 0):
                am -= amPerActivity

            if am <= 0:
                # system failure
                if extend == maxExtends:
                    break

                voyTime = tick / ticksPerHour
                refillCost = math.ceil(voyTime * 60 / dilPerMin)

                if extend <= numExtends:
                    results[extend][iSim] = tick / ticksPerHour
                    if extend > 0:
                        resultsRefillCostTotal[extend] += refillCostTotal

                am = startAm
                refillCostTotal += refillCost
                extend += 1

                if voyTime > 20:
                    results20hrCostTotal += refillCostTotal
                    results20hrRefillsTotal += extend
                    break

                if (extend > numExtends) and (iSim >= num20hourSims):
                    break

    # List<ExtendResult> extendResults = new List<ExtendResult>()
    extendResults = []
    for extend in range(numExtends+1):
        exResults = results[extend]

        exResults.sort()
        voyTime = exResults[math.floor(len(exResults) / 2)]

        # compute other results
        safeTime = exResults[math.floor((len(exResults) / 10))]
        saferTime = exResults[math.floor((len(exResults) / 100))]
        # safestTime = exResults[0]

        # compute last dilemma chance
        lastDilemma = 0
        lastDilemmaFails = 0
        for i in range(len(exResults)):
            dilemma = math.floor(exResults[i] / hoursBetweenDilemmas)
            if dilemma > lastDilemma:
                lastDilemma = dilemma
                lastDilemmaFails = max(0, i)

        dilChance = round((100 * (len(exResults) - lastDilemmaFails) / len(exResults)))
        # HACK: if there is a tiny chance of the next dilemma, assume 100% chance of the previous one instead
        if dilChance == 0:
            lastDilemma -= 1
            dilChance = 100

        extendResult = VoyageResult()
        extendResult.result = voyTime
        extendResult.safeResult = safeTime
        extendResult.saferResult = saferTime
        extendResult.lastDil = lastDilemma * hoursBetweenDilemmas
        extendResult.dilChance = dilChance
        if extend > 0:
            extendResult.refillCostResult = math.ceil(resultsRefillCostTotal[extend] / numSims)

        # the threshold here is just a guess
        '''
        if maxSkill / hazSkillPerHour > voyTime:
            tp = math.floor(voyTime * hazSkillPerHour)
            if currentAm == 0:
                # setWarning(extend, "Your highest skill is too high by about " +
                #       Math.floor(maxSkill - voyTime * hazSkillPerHour) +
                #       ". To maximize voyage time, redistribute more like this: " +
                #       tp + "/" + tp + "/" + tp / 4 + "/" + tp / 4 + "/" + tp / 4 + "/" + tp / 4 + ".");
                pass
        '''

        extendResults.append(extendResult)

    # 20 hour cost (dil) = Math.ceil(results20hrCostTotal / num20hourSims);
    # for this many refills = Math.round(results20hrRefillsTotal / num20hourSims);

    return extendResults


if __name__ == "__main__":
    sample_stats = [13000, 12000, 6000, 5000, 4000, 4000, 2700]
    print(sample_stats)
    print(voyage_estimator_simple(*sample_stats, False))
