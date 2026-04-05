// Sound utility for cinematic audio effects
export const playSound = (soundName) => {
  try {
    const sound = new Audio(`/sounds/${soundName}.mp3`);
    sound.volume = 0.3; // Keep volume moderate
    sound.play().catch(() => {
      // Silently fail if sound doesn't exist or autoplay is blocked
    });
  } catch (err) {
    // Silently fail
  }
};

export const playClickSound = () => playSound('click');
export const playSuccessSound = () => playSound('success');
