import { useState, FormEvent } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  useToast,
} from '@chakra-ui/react';
import { submitQuery } from '../services/api';
import { QueryResponse } from '../types';

interface QueryFormProps {
  onSubmit: (result: QueryResponse) => void;
  onError: (error: Error) => void;
}

export const QueryForm = ({ onSubmit, onError }: QueryFormProps) => {
  const [query, setQuery] = useState('');
  const toast = useToast();

  const mutation = useMutation({
    mutationFn: submitQuery,
    onSuccess: (data) => {
      onSubmit(data);
      toast({
        title: 'Success',
        description: 'Query submitted successfully',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    },
    onError: (error: Error) => {
      onError(error);
    },
  });

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!query.trim()) {
      toast({
        title: 'Error',
        description: 'Please enter a query',
        status: 'error',
        duration: 3000,
        isClosable: true,
      });
      return;
    }
    mutation.mutate(query);
  };

  return (
    <Box as="form" onSubmit={handleSubmit}>
      <VStack spacing={4}>
        <FormControl isRequired>
          <FormLabel>Enter your research query</FormLabel>
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What would you like to know about the research papers?"
            size="lg"
            disabled={mutation.isPending}
          />
        </FormControl>
        <Button
          type="submit"
          colorScheme="blue"
          size="lg"
          width="full"
          isLoading={mutation.isPending}
        >
          Submit Query
        </Button>
      </VStack>
    </Box>
  );
};
