export function generateProfile(aadhaar) {
  const seed = parseInt(aadhaar.slice(-6), 10);

  const maleNames = [
    'Ravi', 'Srinivas', 'Ramesh', 'Prakash', 'Mahesh',
    'Kiran', 'Venkatesh', 'Naresh', 'Rajesh', 'Harish',
    'Chandra', 'Suresh', 'Gopi', 'Srikanth', 'Raghu',
    'Manoj', 'Anil', 'Vamshi', 'Naveen', 'Sai',
  ];
  const femaleNames = [
    'Lakshmi', 'Padma', 'Sravani', 'Swathi', 'Anitha',
    'Deepika', 'Keerthi', 'Bhavani', 'Sowmya', 'Divya',
    'Anjali', 'Harika', 'Tejaswini', 'Sushma', 'Madhavi',
    'Shilpa', 'Kavitha', 'Renuka', 'Sunitha', 'Pooja',
  ];
  const surnames = [
    'Reddy', 'Naidu', 'Rao', 'Yadav', 'Goud',
    'Sharma', 'Kumar', 'Varma', 'Rao', 'Naik',
  ];

  const isFemale = parseInt(aadhaar.slice(-1), 10) % 2 === 0;
  const first = isFemale
    ? femaleNames[seed % femaleNames.length]
    : maleNames[seed % maleNames.length];
  const last = surnames[Math.floor(seed / 10) % surnames.length];
  const name = `${first} ${last}`;

  const gender = isFemale ? 'Female' : 'Male';
  const state = 'Telangana';

  const year = 1975 + (seed % 25);
  const month = String((seed % 12) + 1).padStart(2, '0');
  const day = String((seed % 28) + 1).padStart(2, '0');
  const dob = `${year}-${month}-${day}`;

  const avatar = `https://api.dicebear.com/7.x/initials/svg?seed=${name}`;
  const phone = '9' + String(seed).padStart(9, '0').slice(0, 9);

  return {
    name,
    gender,
    state,
    dob,
    phone,
    phone_masked: 'XXXXXX' + phone.slice(-4),
    avatar,
    aadhaar_masked: 'XXXX-XXXX-' + aadhaar.slice(-4),
  };
}
