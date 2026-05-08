import { createContext, useContext } from "react";
import type { User } from "./types";

export interface AuthContextValue {
  user: User | null;
  loading: boolean;
  refetch: () => void;
}

export const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  refetch: () => {},
});

export const useAuth = () => useContext(AuthContext);

export const MONTH_NAMES = [
  "", "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export const formatPeriod = (month: number, year: number) =>
  `${MONTH_NAMES[month]} ${year}`;
