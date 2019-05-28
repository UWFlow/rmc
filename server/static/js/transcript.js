define(function(require) {
  // Invoke func repeatedly until it runs out of things to return.
  // This is handy for wrapping lambdas for the lack of a () =>* ... shorthand.
  function* asGenerator(func) {
    var res;
    while ((res = func())) yield res;
  }

  // Given `arr`, `other` monotonic and a strict order `lt` denoted <,
  // partition `arr` so that for `x` in `n`th bin `other[n] < x < other[n+1]`.
  function leftMonotonicPartitionBy(arr, other, lt) {
    const partitions = [];
    for (var j = 0, i = 0; j + 1 < other.length; ++j)
      for (partitions[j] = []; i < arr.length && lt(other[j], arr[i]) && lt(arr[i], other[j + 1]); ++i)
        partitions[j].push(arr[i]);
    partitions[j] = arr.slice(i); // rest
    return partitions;
  }

  // Produce {term, level, courses} objects from flat lists of regex matches.
  function assembleSchedule(terms, levels, courses) {
    const coursePartition = leftMonotonicPartitionBy(courses, levels, (a, b) => a.index < b.index);
    // Exclude empty terms: can exist in exchange schenarios.
    levels = levels.filter((_, i) => coursePartition[i].length > 0);
    const coursesByTerm = levels.map((level, i) => ({
      name: terms[i][0], // extract full match
      programYearId: level[1], // extract 1B, 5C, etc
      courseIds: coursePartition[i].map(c => (c[1] + c[2]).toLowerCase()) // MATH 135 => math135
    }));
    return coursesByTerm;
  }

  function extractProgramName(txt) {
    // Find and return the last occurence of Program:(.*)\n
    // This can be done with regexp as well, but the expression is arcane.
    const start = txt.lastIndexOf('Program:') + 'Program:'.length;
    const end = txt.indexOf('\n', start);
    return txt.substr(start, end - start).trimStart();
  }

  function parseTranscript(txt) {
    const termRegex = /(Fall|Winter|Spring)\s+(\d{4})/g;
    // Levels are similar to 1A, 5C (delayed graduation).
    const levelRegex = /Level:\s+(\d\w)/g;
    // Course codes are similar to CS 145, STAT 920, PD 1, CHINA 120R.
    const courseRegex = /([A-Z]{2,})\s+(\d{1,3}\w?)\s/g;

    const studentId = txt.match(/Student ID:\s+(\d+)/);
    const programName = extractProgramName(txt);

    const terms = Array.from(asGenerator(() => termRegex.exec(txt)));
    const levels = Array.from(asGenerator(() => levelRegex.exec(txt)));
    const courses = Array.from(asGenerator(() => courseRegex.exec(txt)));

    return {
      // Flow wants schedule in reverse order
      coursesByTerm: assembleSchedule(terms, levels, courses).reverse(),
      studentId: Number.parseInt(studentId[1]),
      // Spaces can be missing, so split on UpperCamelCase.
      programName: programName.split(/(?<=[a-z,])(?=[A-Z])/).join(" ")
    };
  }

  function removeGrades(txt) {
    // Lines start with course subject (like MATH) and end with grade like 94 or NCR.
    return txt.replace(/(?<=^[A-Z]{2,}.*)\s+(\w{2,3}|\d{1,3})$/gm, "");
  }

  return {
    parseTranscript: parseTranscript,
    removeGrades: removeGrades
  };
});
